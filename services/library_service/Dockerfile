FROM python:3.12-slim

WORKDIR /app

# Cài đặt công cụ hệ thống cần thiết (curl cho healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt Python dependencies
COPY services/library_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code và cấu hình
COPY services/library_service/alembic.ini ./alembic.ini
COPY services/library_service/alembic ./alembic
COPY services/library_service/src ./services/library_service/src

# Set Python path để import module chính xác
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8001

CMD ["uvicorn", "services.library_service.src.main:app", "--host", "0.0.0.0", "--port", "8001"]

