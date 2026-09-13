from fastapi import APIRouter
from services.reservation_service.src.core.config import settings
from services.reservation_service.src.core.redis_client import redis_manager
from services.reservation_service.src.kafka.consumer import kafka_consumer_worker
from services.reservation_service.src.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    # 1. Kiểm tra Redis ping
    is_redis_alive = await redis_manager.ping()
    redis_status = "connected" if is_redis_alive else "disconnected"

    # 2. Kiểm tra Kafka Consumer
    kafka_status = "running" if kafka_consumer_worker.is_running else "stopped/standalone"

    overall_status = "ok" if is_redis_alive else "degraded"

    return HealthResponse(
        service=settings.APP_NAME,
        status=overall_status,
        dependencies={
            "redis": redis_status,
            "kafka_consumer": kafka_status,
        }
    )


