"""日志配置。"""
import logging
import sys

from app.core.config import settings

LOGGING_LEVEL = logging.DEBUG if settings.DEBUG else logging.INFO


def setup_logging() -> None:
    logging.basicConfig(
        level=LOGGING_LEVEL,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        stream=sys.stdout,
    )


setup_logging()
