from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.reservation_service.src.core.config import settings
from services.reservation_service.src.core.logging import setup_logging, logger
from services.reservation_service.src.core.redis_client import redis_manager
from services.reservation_service.src.services.queue_service import queue_service
from services.reservation_service.src.api.health import router as health_router
from services.reservation_service.src.api.reservations import router as reservations_router

# Thiết lập logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi động kết nối Redis
    logger.info(f"Starting {settings.APP_NAME} in '{settings.APP_ENV}' environment...")
    await redis_manager.connect()
    if redis_manager.client:
        queue_service.set_redis_client(redis_manager.client)

    yield

    # Đóng kết nối Redis
    logger.info(f"Shutting down {settings.APP_NAME}...")
    await redis_manager.disconnect()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Reservation Service handling async queues and fast status queries via Redis.",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký routes
app.include_router(health_router, prefix="/api/v1")
app.include_router(health_router)
app.include_router(reservations_router, prefix="/api/v1")
app.include_router(reservations_router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": settings.APP_NAME,
        "status": "running",
        "docs_url": "/docs",
    }

