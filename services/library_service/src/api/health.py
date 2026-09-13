from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from services.library_service.src.core.database import get_db
from services.library_service.src.core.config import settings
from services.library_service.src.kafka.producer import kafka_producer
from services.library_service.src.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    # 1. Kiểm tra kết nối Database
    db_status = "unhealthy"
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    # 2. Kiểm tra trạng thái Kafka Producer
    kafka_status = "connected" if kafka_producer.is_connected else "disconnected/standalone"

    overall_status = "ok" if db_status == "connected" else "degraded"

    return HealthResponse(
        service=settings.APP_NAME,
        status=overall_status,
        dependencies={
            "database": db_status,
            "kafka_producer": kafka_status,
        }
    )

