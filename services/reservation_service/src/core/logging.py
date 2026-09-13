import logging
import sys
from services.reservation_service.src.core.config import settings


def setup_logging():
    log_format = "%(asctime)s [%(levelname)s] [ReservationService] %(name)s: %(message)s"
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    if not settings.DEBUG:
        logging.getLogger("aiokafka").setLevel(logging.WARNING)


logger = logging.getLogger("reservation_service")

