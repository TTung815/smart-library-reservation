import asyncio
import json
from typing import Optional
from aiokafka import AIOKafkaConsumer
from services.reservation_service.src.core.config import settings
from services.reservation_service.src.core.logging import logger, request_id_context
from services.reservation_service.src.services.queue_service import queue_service



class KafkaConsumerWorker:
    def __init__(self):
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.task: Optional[asyncio.Task] = None
        self.is_running: bool = False

    async def start(self):
        """Khởi động Kafka Consumer và tạo background task lắng nghe sự kiện."""
        if not settings.KAFKA_ENABLED:
            logger.info("Kafka is disabled in settings. Skipping Kafka Consumer startup.")
            return

        try:
            self.consumer = AIOKafkaConsumer(
                settings.KAFKA_TOPIC_RESERVATIONS,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=settings.KAFKA_GROUP_ID,
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                key_deserializer=lambda k: k.decode("utf-8") if k else None,
            )
            await self.consumer.start()
            self.is_running = True
            logger.info(
                f"Kafka Consumer started. Subscribed to topic '{settings.KAFKA_TOPIC_RESERVATIONS}', "
                f"group='{settings.KAFKA_GROUP_ID}'"
            )
            # Chạy loop tiêu thụ event trong một background asyncio task
            self.task = asyncio.create_task(self._consume_loop())
        except Exception as e:
            self.is_running = False
            logger.warning(
                f"Could not connect Kafka Consumer to {settings.KAFKA_BOOTSTRAP_SERVERS}: {e}. "
                f"Consumer worker will not start in standalone mode."
            )

    async def _consume_loop(self):
        """Vòng lặp bất đồng bộ liên tục đọc message từ Kafka partition."""
        logger.info("Kafka Consumer loop running...")
        try:
            async for msg in self.consumer:
                if not self.is_running:
                    break
                try:
                    await self.process_message(msg.value)
                except Exception as e:
                    logger.error(f"Error processing Kafka message: {e}", exc_info=True)
        except asyncio.CancelledError:
            logger.info("Kafka Consumer loop cancelled.")
        except Exception as e:
            logger.error(f"Unexpected error in Kafka Consumer loop: {e}")
        finally:
            logger.info("Kafka Consumer loop finished.")

    async def process_message(self, message_data: dict) -> bool:
        """
        Xử lý sự kiện nhận được từ Kafka:
        - Thiết lập correlation ID từ event_id vào log context
        - Kiểm tra event_type
        - Trích xuất dữ liệu reservation_id, user_id, book_id
        - Thêm vào hàng đợi Redis và lưu trạng thái WAITING
        """
        event_id = message_data.get("event_id", "-")
        trace_token = request_id_context.set(event_id[:10] if event_id != "-" else "-")
        try:
            logger.info(f"[KafkaConsumer] Incoming event: {message_data}")

            event_type = message_data.get("event_type")
            if event_type != "BookReservationRequested":
                logger.warning(f"Ignored unknown event_type: {event_type}")
                return False

            payload = message_data.get("data", {})
            reservation_id = payload.get("reservation_id")
            user_id = payload.get("user_id")
            book_id = payload.get("book_id")

            if not all([reservation_id, user_id, book_id]):
                logger.error(f"Missing required fields in payload: {payload}")
                return False

            # Đưa vào hàng đợi Redis
            reservation = await queue_service.add_reservation(
                reservation_id=int(reservation_id),
                user_id=int(user_id),
                book_id=int(book_id),
            )

            logger.info(
                f"[KafkaConsumer] Successfully queued reservation {reservation.reservation_id} "
                f"for book {reservation.book_id}. Queue position: {reservation.position}"
            )
            return True
        finally:
            request_id_context.reset(trace_token)


    async def stop(self):
        """Dừng Consumer worker một cách an toàn (graceful shutdown)."""
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        if self.consumer:
            try:
                await self.consumer.stop()
                logger.info("Kafka Consumer stopped successfully.")
            except Exception as e:
                logger.warning(f"Error stopping Kafka Consumer: {e}")


kafka_consumer_worker = KafkaConsumerWorker()

