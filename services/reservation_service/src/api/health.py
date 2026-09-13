import time
from fastapi import APIRouter, Response, status
from services.reservation_service.src.core.config import settings
from services.reservation_service.src.core.redis_client import redis_manager
from services.reservation_service.src.kafka.consumer import kafka_consumer_worker
from services.reservation_service.src.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(response: Response):
    dependencies = {}
    is_healthy = True

    # 1. Kiểm tra kết nối Redis và đo ping latency
    try:
        start_time = time.perf_counter()
        is_redis_alive = await redis_manager.ping()
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        if is_redis_alive:
            dependencies["redis"] = {
                "status": "connected",
                "latency_ms": latency_ms,
            }
        else:
            is_healthy = False
            dependencies["redis"] = {
                "status": "disconnected",
            }
    except Exception as e:
        is_healthy = False
        dependencies["redis"] = {
            "status": "error",
            "error": str(e),
        }

    # 2. Kiểm tra trạng thái Kafka Consumer Worker
    consumer_status = "running" if kafka_consumer_worker.is_running else "stopped/standalone"
    dependencies["kafka_consumer"] = {
        "status": consumer_status,
    }

    overall_status = "healthy" if is_healthy else "degraded"
    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        service=settings.APP_NAME,
        status=overall_status,
        environment=settings.APP_ENV,
        dependencies=dependencies,
    )
