import json
from datetime import datetime, timezone
from typing import Optional, List
import redis.asyncio as aioredis
from services.reservation_service.src.core.logging import logger
from services.reservation_service.src.schemas.reservation import ReservationDetail


class ReservationQueueService:
    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        self.redis = redis_client

    def set_redis_client(self, client: aioredis.Redis):
        self.redis = client

    def _queue_key(self, book_id: int) -> str:
        return f"book_queue:{book_id}"

    def _reservation_key(self, reservation_id: int) -> str:
        return f"reservation:{reservation_id}"

    async def add_reservation(self, reservation_id: int, user_id: int, book_id: int) -> ReservationDetail:
        """
        Đưa reservation vào hàng đợi FIFO trong Redis:
        1. RPUSH vào danh sách 'book_queue:{book_id}'
        2. LPOS để xác định vị trí trong hàng đợi (1-indexed)
        3. Lưu snapshot thông tin vào key 'reservation:{reservation_id}'
        """
        if not self.redis:
            raise RuntimeError("Redis client is not initialized or connected")

        queue_key = self._queue_key(book_id)
        res_key = self._reservation_key(reservation_id)
        str_res_id = str(reservation_id)

        # Kiểm tra xem reservation_id đã có trong queue chưa để tránh trùng lặp
        pos = await self.redis.lpos(queue_key, str_res_id)
        if pos is None:
            # Thêm vào cuối hàng đợi (FIFO: RPUSH)
            await self.redis.rpush(queue_key, str_res_id)
            pos = await self.redis.lpos(queue_key, str_res_id)

        position = (pos if pos is not None else 0) + 1
        now_iso = datetime.now(timezone.utc).isoformat()

        reservation_data = {
            "reservation_id": reservation_id,
            "user_id": user_id,
            "book_id": book_id,
            "status": "WAITING",
            "position": position,
            "created_at": now_iso,
            "updated_at": now_iso,
        }

        # Lưu thông tin chi tiết vào Redis
        await self.redis.set(res_key, json.dumps(reservation_data))

        logger.info(
            f"[QueueService] Enqueued reservation_id={reservation_id} for book_id={book_id}. "
            f"Queue position: {position}"
        )

        return ReservationDetail(**reservation_data)

    async def get_reservation(self, reservation_id: int) -> Optional[ReservationDetail]:
        """
        Tra cứu nhanh thông tin đặt chỗ từ Redis:
        - Đọc JSON từ 'reservation:{reservation_id}'
        - Tái tính toán vị trí động bằng LPOS trên 'book_queue:{book_id}'
        """
        if not self.redis:
            raise RuntimeError("Redis client is not initialized or connected")

        res_key = self._reservation_key(reservation_id)
        raw_data = await self.redis.get(res_key)
        if not raw_data:
            return None

        data = json.loads(raw_data)
        book_id = data.get("book_id")
        str_res_id = str(reservation_id)

        # Cập nhật lại vị trí hàng đợi mới nhất theo thời gian thực
        if book_id:
            queue_key = self._queue_key(book_id)
            pos = await self.redis.lpos(queue_key, str_res_id)
            if pos is not None:
                data["position"] = pos + 1
            else:
                data["status"] = "PROCESSED"
                data["position"] = 0

        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        return ReservationDetail(**data)

    async def get_book_queue(self, book_id: int) -> List[int]:
        """Lấy toàn bộ danh sách reservation_id đang chờ của một cuốn sách."""
        if not self.redis:
            return []
        queue_key = self._queue_key(book_id)
        items = await self.redis.lrange(queue_key, 0, -1)
        return [int(item) for item in items]


queue_service = ReservationQueueService()

