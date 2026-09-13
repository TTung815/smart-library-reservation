import logging
import sys
from contextvars import ContextVar
from services.library_service.src.core.config import settings

# ContextVar lưu trữ correlation_id / request_id xuyên suốt async coroutines
request_id_context: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_context.get()
        return True


def setup_logging():
    log_format = "%(asctime)s [%(levelname)s] [LibraryService] [trace_id=%(request_id)s] %(name)s: %(message)s"
    formatter = logging.Formatter(log_format)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    # Xóa handler cũ nếu có
    root_logger.handlers = [handler]

    if not settings.DEBUG:
        logging.getLogger("aiokafka").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


logger = logging.getLogger("library_service")
