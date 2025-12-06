"""Structured logging helpers."""

import logging
import time
from typing import Optional

from youtube_search.config import get_settings

LOG_FORMAT = (
    "%(asctime)s %(levelname)s %(name)s "
    "%(message)s [%(filename)s:%(lineno)d %(funcName)s]"
)
DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def configure_logging(level: Optional[str] = None) -> None:
    """Configure root logger with UTC timestamps."""

    settings = get_settings()
    effective_level = (level or settings.api_log_level).upper()
    logging.Formatter.converter = time.gmtime
    logging.basicConfig(level=effective_level, format=LOG_FORMAT, datefmt=DATE_FORMAT)


def get_logger(name: str) -> logging.Logger:
    """Return module logger ensuring base configuration exists."""

    if not logging.getLogger().handlers:
        configure_logging()
    return logging.getLogger(name)
