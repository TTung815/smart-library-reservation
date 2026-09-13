import logging
import sys
from contextvars import ContextVar
from services.reservation_service.src.core.config import settings

# ContextVar lưu trữ correlation_id / request_id
request_id_context: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_context.get()
        return True


def setup_logging():
    log_format = "%(asctime)s [%(levelname)s] [ReservationService] [trace_id=%(request_id)s] %(name)s: %(message)s"
    formatter = logging.Formatter(log_format)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    root_logger.handlers = [handler]

    if not settings.DEBUG:
        logging.getLogger("aiokafka").setLevel(logging.WARNING)


logger = logging.getLogger("reservation_service")
