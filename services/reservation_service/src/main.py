import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from services.reservation_service.src.core.config import settings
from services.reservation_service.src.core.logging import setup_logging, logger, request_id_context
from services.reservation_service.src.core.redis_client import redis_manager
from services.reservation_service.src.services.queue_service import queue_service
from services.reservation_service.src.kafka.consumer import kafka_consumer_worker
from services.reservation_service.src.api.health import router as health_router
from services.reservation_service.src.api.reservations import router as reservations_router

# Thiết lập logging
setup_logging()


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:10]
        token = request_id_context.set(req_id)
        try:
            response: Response = await call_next(request)
            response.headers["X-Request-ID"] = req_id
            return response
        finally:
            request_id_context.reset(token)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} in '{settings.APP_ENV}' environment...")
    await redis_manager.connect()
    if redis_manager.client:
        queue_service.set_redis_client(redis_manager.client)

    await kafka_consumer_worker.start()

    yield

    logger.info(f"Shutting down {settings.APP_NAME}...")
    await kafka_consumer_worker.stop()
    await redis_manager.disconnect()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Reservation Service handling async queues and fast status queries via Redis.",
    lifespan=lifespan,
)

# Middleware truy vết Correlation ID
app.add_middleware(RequestIDMiddleware)

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
