"""Structured logging helpers."""

import logging
import time
from typing import Optional

from youtube_search.config import get_settings

# ANSI color codes
COLORS = {
    "DEBUG": "\033[36m",  # Cyan
    "INFO": "\033[32m",  # Green
    "WARNING": "\033[33m",  # Yellow
    "ERROR": "\033[31m",  # Red
    "CRITICAL": "\033[35m",  # Magenta
    "RESET": "\033[0m",  # Reset
    "BOLD": "\033[1m",  # Bold
    "DIM": "\033[2m",  # Dim
}

LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)-30s %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class ExtraFormatter(logging.Formatter):
    """Custom formatter with colors and structured extra fields."""

    def format(self, record: logging.LogRecord) -> str:
        # Add color to level name
        levelname = record.levelname
        if levelname in COLORS:
            record.levelname = f"{COLORS[levelname]}{COLORS['BOLD']}{levelname}{COLORS['RESET']}"

        # Format base message
        base_msg = super().format(record)

        # Add location info (dimmed)
        location = (
            f"{COLORS['DIM']}[{record.filename}:{record.lineno} {record.funcName}]{COLORS['RESET']}"
        )

        # Collect extra fields (exclude standard LogRecord attributes)
        standard_attrs = {
            "name", "msg", "args", "created", "filename", "funcName", "levelname",
            "levelno", "lineno", "module", "msecs", "message", "pathname", "process",
            "processName", "relativeCreated", "thread", "threadName", "exc_info",
            "exc_text", "stack_info", "asctime",
        }

        extra_items = {
            k: v
            for k, v in record.__dict__.items()
            if k not in standard_attrs and not k.startswith("_") and k != "taskName"
        }

        # Format extra fields with colors
        if extra_items:
            extra_parts = []
            for k, v in sorted(extra_items.items()):
                key_colored = f"{COLORS['DIM']}{k}{COLORS['RESET']}"
                if k in ("error", "error_type", "dns_error"):
                    value_colored = f"{COLORS['ERROR']}{v}{COLORS['RESET']}"
                elif k in ("status", "resolved_ip"):
                    value_colored = f"{COLORS['INFO']}{v}{COLORS['RESET']}"
                else:
                    value_colored = str(v)
                extra_parts.append(f"{key_colored}={value_colored}")

            extra_str = " ".join(extra_parts)
            return f"{base_msg} {location}\n    {COLORS['DIM']}↳{COLORS['RESET']} {extra_str}"

        return f"{base_msg} {location}"


def configure_logging(level: Optional[str] = None) -> None:
    """Configure root logger with UTC timestamps."""

    settings = get_settings()
    effective_level = (level or settings.api_log_level).upper()
    logging.Formatter.converter = time.gmtime

    # Remove existing handlers to avoid duplicates
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Configure with custom formatter
    handler = logging.StreamHandler()
    handler.setFormatter(ExtraFormatter(LOG_FORMAT, DATE_FORMAT))
    root_logger.addHandler(handler)
    root_logger.setLevel(effective_level)


def get_logger(name: str) -> logging.Logger:
    """Return module logger ensuring base configuration exists."""

    if not logging.getLogger().handlers:
        configure_logging()
    return logging.getLogger(name)
