from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.library_service.src.core.config import settings
from services.library_service.src.core.logging import setup_logging, logger
from services.library_service.src.kafka.producer import kafka_producer
from services.library_service.src.api.health import router as health_router
from services.library_service.src.api.books import router as books_router
from services.library_service.src.api.borrow import router as borrow_router

# Thiết lập logging chuẩn
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi động: Kết nối Kafka Producer
    logger.info(f"Starting {settings.APP_NAME} in '{settings.APP_ENV}' environment...")
    await kafka_producer.start()

    yield

    # Dừng: Đóng kết nối Kafka Producer
    logger.info(f"Shutting down {settings.APP_NAME}...")
    await kafka_producer.stop()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Library Management Service handling books, borrowings, and reservation requests.",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký routes (cả trực tiếp và theo prefix /api/v1 để tương thích Nginx)
app.include_router(health_router, prefix="/api/v1")
app.include_router(health_router)  # Cho phép gọi trực tiếp /health
app.include_router(books_router, prefix="/api/v1")
app.include_router(books_router)   # Cho phép gọi trực tiếp /books
app.include_router(borrow_router, prefix="/api/v1")
app.include_router(borrow_router)  # Cho phép gọi trực tiếp /borrow


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": settings.APP_NAME,
        "status": "running",
        "docs_url": "/docs",
    }

