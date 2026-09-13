import pytest
import pytest_asyncio
import fakeredis.aioredis as fake_aioredis
from httpx import AsyncClient, ASGITransport
from services.reservation_service.src.main import app
from services.reservation_service.src.core.redis_client import redis_manager
from services.reservation_service.src.services.queue_service import queue_service, ReservationQueueService


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
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_reservation_root_endpoint(res_client: AsyncClient):
    response = await res_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Reservation Service"
    assert data["status"] == "running"


@pytest.mark.asyncio
async def test_queue_service_uninitialized_redis():
    # Service không có redis client phải raise RuntimeError
    uninit_service = ReservationQueueService(redis_client=None)
    with pytest.raises(RuntimeError):
        await uninit_service.add_reservation(1, 1, 1)

    with pytest.raises(RuntimeError):
        await uninit_service.get_reservation(1)

    queue = await uninit_service.get_book_queue(1)
    assert queue == []


@pytest.mark.asyncio
async def test_dynamic_queue_repositioning(res_client: AsyncClient, fake_redis):
    """Khi người đứng trước được xử lý/bỏ khỏi queue, người đứng sau tự động tiến lên vị trí trước."""
    # User 10 và User 11 cùng đặt sách 99
    res1 = await queue_service.add_reservation(reservation_id=301, user_id=10, book_id=99)
    res2 = await queue_service.add_reservation(reservation_id=302, user_id=11, book_id=99)

    assert res1.position == 1
    assert res2.position == 2

    # Giả lập người đầu tiên (301) đã được thỏa mãn (LPOP khỏi queue)
    await fake_redis.lpop("book_queue:99")

    # Kiểm tra lại vị trí của người thứ 2 (302) -> phải tự động lên số 1!
    updated_res2 = await queue_service.get_reservation(302)
    assert updated_res2 is not None
    assert updated_res2.position == 1

    # Kiểm tra qua API endpoint
    resp = await res_client.get("/api/v1/reservations/302")
    assert resp.status_code == 200
    assert resp.json()["position"] == 1


@pytest.mark.asyncio
async def test_health_check_redis_disconnected(res_client: AsyncClient):
    """Khi Redis bị ngắt kết nối, Health Check phải trả về 503 và trạng thái degraded/disconnected."""
    redis_manager.client = None
    redis_manager.is_connected = False

    response = await res_client.get("/api/v1/health")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert data["dependencies"]["redis"]["status"] == "disconnected"
