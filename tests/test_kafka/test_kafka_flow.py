import pytest
import pytest_asyncio
import fakeredis.aioredis as fake_aioredis
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from services.library_service.src.kafka.producer import kafka_producer
from services.reservation_service.src.kafka.consumer import kafka_consumer_worker
from services.reservation_service.src.services.queue_service import queue_service
from services.reservation_service.src.core.redis_client import redis_manager
from services.reservation_service.src.main import app as res_app


@pytest_asyncio.fixture
async def fake_redis():
    server = fake_aioredis.FakeServer()
    client = fake_aioredis.FakeRedis(server=server, decode_responses=True)
    redis_manager.client = client
    redis_manager.is_connected = True
    queue_service.set_redis_client(client)

    yield client

    await client.flushall()
    if hasattr(client, "aclose"):
        await client.aclose()
    else:
        await client.close()


@pytest_asyncio.fixture
async def res_client(fake_redis):
    transport = ASGITransport(app=res_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_kafka_producer_event_contract():
    """Kiểm tra cấu trúc event payload và partition key do Producer tạo ra."""
    with patch.object(kafka_producer, "producer", new_callable=AsyncMock) as mock_aiokafka:
        kafka_producer.is_connected = True
        mock_aiokafka.send_and_wait = AsyncMock()

        success = await kafka_producer.publish_reservation_requested(
            reservation_id=123,
            user_id=101,
            book_id=25,
        )

        assert success is True
        assert mock_aiokafka.send_and_wait.called

        # Kiểm tra tham số gọi sang Kafka broker
        call_args = mock_aiokafka.send_and_wait.call_args
        topic = call_args.kwargs.get("topic")
        key = call_args.kwargs.get("key")
        value = call_args.kwargs.get("value")

        assert topic == "book-reservations"
        assert key == "25"  # Key là book_id dạng string để route cùng partition
        assert value["event_type"] == "BookReservationRequested"
        assert value["data"]["reservation_id"] == 123
        assert value["data"]["user_id"] == 101
        assert value["data"]["book_id"] == 25
        assert "event_id" in value
        assert "timestamp" in value


@pytest.mark.asyncio
async def test_kafka_consumer_process_valid_event(fake_redis, res_client: AsyncClient):
    """Kiểm tra Consumer tiếp nhận message và cập nhật chính xác vào Redis."""
    event_message = {
        "event_id": "test-uuid-1",
        "event_type": "BookReservationRequested",
        "timestamp": "2026-09-13T20:00:00Z",
        "data": {
            "reservation_id": 999,
            "user_id": 55,
            "book_id": 42,
        },
    }

    # Consumer xử lý message
    processed = await kafka_consumer_worker.process_message(event_message)
    assert processed is True

    # Kiểm tra Redis có dữ liệu
    res = await queue_service.get_reservation(999)
    assert res is not None
    assert res.reservation_id == 999
    assert res.user_id == 55
    assert res.book_id == 42
    assert res.status == "WAITING"
    assert res.position == 1

    # Kiểm tra qua API tra cứu của Reservation Service
    api_resp = await res_client.get("/api/v1/reservations/999")
    assert api_resp.status_code == 200
    assert api_resp.json()["status"] == "WAITING"
    assert api_resp.json()["position"] == 1


@pytest.mark.asyncio
async def test_kafka_consumer_ignores_unknown_event(fake_redis):
    """Consumer phải bỏ qua an toàn các event không đúng loại."""
    bad_event = {
        "event_type": "UnknownEventType",
        "data": {"foo": "bar"},
    }
    processed = await kafka_consumer_worker.process_message(bad_event)
    assert processed is False


@pytest.mark.asyncio
async def test_kafka_consumer_handles_missing_fields(fake_redis):
    """Consumer xử lý an toàn khi payload bị thiếu thông tin."""
    corrupted_event = {
        "event_type": "BookReservationRequested",
        "data": {
            "reservation_id": 123,
            # Thiếu user_id và book_id
        },
    }
    processed = await kafka_consumer_worker.process_message(corrupted_event)
    assert processed is False


@pytest.mark.asyncio
async def test_end_to_end_async_flow(fake_redis, res_client: AsyncClient):
    """
    Mô phỏng toàn bộ luồng E2E:
    Library Service hết sách -> Tạo event -> Consumer nhận -> Redis cập nhật -> Client query
    """
    captured_event = {}

    # Mock send_and_wait để bắt payload được emit ra
    async def capture_send(topic, key, value):
        captured_event["topic"] = topic
        captured_event["key"] = key
        captured_event["value"] = value

    with patch.object(kafka_producer, "producer", new_callable=AsyncMock) as mock_aiokafka:
        kafka_producer.is_connected = True
        mock_aiokafka.send_and_wait = capture_send

        # 1. Library Service publish event
        await kafka_producer.publish_reservation_requested(
            reservation_id=888,
            user_id=77,
            book_id=99,
        )

        assert captured_event["key"] == "99"
        assert captured_event["value"]["data"]["reservation_id"] == 888

    # 2. Reservation Consumer tiêu thụ event vừa sinh ra
    success = await kafka_consumer_worker.process_message(captured_event["value"])
    assert success is True

    # 3. Client tra cứu trạng thái reservation qua Reservation Service
    response = await res_client.get("/api/v1/reservations/888")
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["reservation_id"] == 888
    assert res_data["status"] == "WAITING"
    assert res_data["position"] == 1

