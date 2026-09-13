import time
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from services.library_service.src.core.database import get_db
from services.library_service.src.core.config import settings
from services.library_service.src.kafka.producer import kafka_producer
from services.library_service.src.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(response: Response, db: AsyncSession = Depends(get_db)):
    dependencies = {}
    is_healthy = True

    # 1. Kiểm tra kết nối PostgreSQL và đo latency
    try:
        start_time = time.perf_counter()
        await db.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        dependencies["database"] = {
            "status": "connected",
            "latency_ms": latency_ms,
        }
    except Exception as e:
        is_healthy = False
        dependencies["database"] = {
            "status": "error",
            "error": str(e),
        }

    # 2. Kiểm tra trạng thái Kafka Producer
    producer_status = "connected" if kafka_producer.is_connected else "disconnected/standalone"
    dependencies["kafka_producer"] = {
        "status": producer_status,
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
