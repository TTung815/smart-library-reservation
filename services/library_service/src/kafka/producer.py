import json
import uuid
from datetime import datetime, timezone
from typing import Optional
from aiokafka import AIOKafkaProducer
from services.library_service.src.core.config import settings
from services.library_service.src.core.logging import logger


class KafkaProducerService:
    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None
        self.is_connected: bool = False

    async def start(self):
        if not settings.KAFKA_ENABLED:
            logger.info("Kafka is disabled in settings.")
            return

        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: str(k).encode("utf-8") if k is not None else None,
                request_timeout_ms=3000,
            )
            await self.producer.start()
            self.is_connected = True
            logger.info(f"Kafka Producer connected successfully to {settings.KAFKA_BOOTSTRAP_SERVERS}")
        except Exception as e:
            self.is_connected = False
            logger.warning(f"Could not connect Kafka Producer to {settings.KAFKA_BOOTSTRAP_SERVERS}: {e}. Running in standalone mode.")

    async def stop(self):
        if self.producer and self.is_connected:
            try:
                await self.producer.stop()
                logger.info("Kafka Producer stopped.")
            except Exception as e:
                logger.warning(f"Error stopping Kafka Producer: {e}")
            finally:
                self.is_connected = False

    async def publish_reservation_requested(self, reservation_id: int, user_id: int, book_id: int) -> bool:
        """
        Publish sự kiện 'BookReservationRequested' với partition key là book_id.
        Đảm bảo các yêu cầu đặt trước của cùng một cuốn sách luôn vào cùng 1 partition
        để giữ thứ tự FIFO.
        """
        event_payload = {
            "event_id": str(uuid.uuid4()),
            "event_type": "BookReservationRequested",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "reservation_id": reservation_id,
                "user_id": user_id,
                "book_id": book_id,
            }
        }

        logger.info(f"Emitting Kafka event BookReservationRequested: {event_payload}")

        if self.producer and self.is_connected:
            try:
                await self.producer.send_and_wait(
                    topic=settings.KAFKA_TOPIC_RESERVATIONS,
                    key=str(book_id),
                    value=event_payload,
                )
                logger.info(f"Kafka event published to topic '{settings.KAFKA_TOPIC_RESERVATIONS}' with key '{book_id}'")
                return True
            except Exception as e:
                logger.error(f"Failed to publish event to Kafka: {e}")
                return False
        else:
            logger.info(f"[Standalone/DryRun] Kafka not connected. Simulated event publication: {event_payload}")
            return True


kafka_producer = KafkaProducerService()

