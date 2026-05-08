import logging
import sys
from typing import Any

from pythonjsonlogger import jsonlogger

from platform_core.core.config import get_settings


class RequestContextFilter(logging.Filter):
    """Ensures structured logs always expose service metadata."""

    def filter(self, record: logging.LogRecord) -> bool:
        settings = get_settings()
        record.service = settings.app_name
        record.environment = settings.environment
        return True


def configure_logging() -> None:
    settings = get_settings()
    root = logging.getLogger()
    root.setLevel(settings.log_level.upper())
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestContextFilter())

    if settings.log_json:
        formatter: logging.Formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s %(service)s %(environment)s"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        )

    handler.setFormatter(formatter)
    root.addHandler(handler)


def get_logger(name: str, **context: Any) -> logging.LoggerAdapter:
    return logging.LoggerAdapter(logging.getLogger(name), context)
