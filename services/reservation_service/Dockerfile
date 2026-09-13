FROM python:3.12-slim

WORKDIR /app

# Cài đặt công cụ hệ thống cần thiết (curl cho healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt Python dependencies
COPY services/reservation_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY services/reservation_service/src ./services/reservation_service/src

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8002

CMD ["uvicorn", "services.reservation_service.src.main:app", "--host", "0.0.0.0", "--port", "8002"]

