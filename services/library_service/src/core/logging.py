import logging
import sys
from services.library_service.src.core.config import settings


def setup_logging():
    log_format = "%(asctime)s [%(levelname)s] [LibraryService] %(name)s: %(message)s"
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    # Tắt log quá chi tiết của thư viện bên thứ 3 nếu không ở debug mode
    if not settings.DEBUG:
        logging.getLogger("aiokafka").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


logger = logging.getLogger("library_service")

