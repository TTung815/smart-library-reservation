import pytest
import pytest_asyncio
import fakeredis.aioredis as fake_aioredis
from httpx import AsyncClient, ASGITransport
from services.reservation_service.src.main import app
from services.reservation_service.src.core.redis_client import redis_manager
from services.reservation_service.src.services.queue_service import queue_service


@pytest_asyncio.fixture
async def fake_redis():
    server = fake_aioredis.FakeServer()
    client = fake_aioredis.FakeRedis(server=server, decode_responses=True)
    # Gắn fake redis vào redis_manager và queue_service
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
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_reservation_health_check(res_client: AsyncClient, fake_redis):
    response = await res_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Reservation Service"
    assert data["status"] == "healthy"
    assert data["dependencies"]["redis"]["status"] == "connected"
    assert "latency_ms" in data["dependencies"]["redis"]
    assert "x-request-id" in response.headers



@pytest.mark.asyncio
async def test_enqueue_single_reservation(res_client: AsyncClient, fake_redis):
    # Đưa 1 reservation vào queue
    res = await queue_service.add_reservation(reservation_id=101, user_id=1, book_id=25)
    assert res.reservation_id == 101
    assert res.status == "WAITING"
    assert res.position == 1

    # Tra cứu thông qua API GET /api/v1/reservations/101
    response = await res_client.get("/api/v1/reservations/101")
    assert response.status_code == 200
    data = response.json()
    assert data["reservation_id"] == 101
    assert data["user_id"] == 1
    assert data["book_id"] == 25
    assert data["status"] == "WAITING"
    assert data["position"] == 1


@pytest.mark.asyncio
async def test_enqueue_multiple_reservations_fifo_ordering(res_client: AsyncClient, fake_redis):
    # Cuốn sách 25 có 3 người đặt theo thứ tự
    res1 = await queue_service.add_reservation(reservation_id=201, user_id=10, book_id=25)
    res2 = await queue_service.add_reservation(reservation_id=202, user_id=11, book_id=25)
    res3 = await queue_service.add_reservation(reservation_id=203, user_id=12, book_id=25)

    # Kiểm tra thứ tự position tương ứng 1, 2, 3
    assert res1.position == 1
    assert res2.position == 2
    assert res3.position == 3

    # Kiểm tra danh sách hàng đợi trong Redis
    queue_items = await queue_service.get_book_queue(book_id=25)
    assert queue_items == [201, 202, 203]

    # Kiểm tra API tra cứu vị trí của người thứ 2
    resp2 = await res_client.get("/api/v1/reservations/202")
    assert resp2.status_code == 200
    assert resp2.json()["position"] == 2


@pytest.mark.asyncio
async def test_reservation_not_found(res_client: AsyncClient, fake_redis):
    response = await res_client.get("/api/v1/reservations/99999")
    assert response.status_code == 404
    assert "Reservation 99999 not found" in response.json()["detail"]
