from typing import Optional
import redis.asyncio as aioredis
from services.reservation_service.src.core.config import settings
from services.reservation_service.src.core.logging import logger


class RedisClient:
    def __init__(self):
        self.client: Optional[aioredis.Redis] = None
        self.is_connected: bool = False

    async def connect(self):
        try:
            self.client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                health_check_interval=30,
            )
            # Test ping
            await self.client.ping()
            self.is_connected = True
            logger.info(f"Connected to Redis successfully at {settings.REDIS_URL}")
        except Exception as e:
            self.is_connected = False
            logger.warning(f"Could not connect to Redis at {settings.REDIS_URL}: {e}")

    async def disconnect(self):
        if self.client:
            try:
                if hasattr(self.client, "aclose"):
                    await self.client.aclose()
                else:
                    await self.client.close()
                logger.info("Closed Redis connection.")
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")
            finally:
                self.is_connected = False


    async def ping(self) -> bool:
        if not self.client:
            return False
        try:
            return await self.client.ping()
        except Exception:
            return False


redis_manager = RedisClient()


async def get_redis_client() -> Optional[aioredis.Redis]:
    """Dependency cung cấp client Redis."""
    return redis_manager.client
