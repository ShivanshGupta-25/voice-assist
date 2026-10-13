"""Centralized logging configuration."""

import json
import logging
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path


class JsonFormatter(logging.Formatter):
    """Format log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        """Convert a log record into a JSON string."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_entry["exception"] = self.formatException(
                record.exc_info
            )

        return json.dumps(log_entry, ensure_ascii=False)


def configure_logging(
    level: str,
    log_file: Path,
) -> None:
    """Configure console and rotating file logging."""
    log_file.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())

    # Remove only handlers previously installed by this application.
    for handler in root_logger.handlers[:]:
        if getattr(handler, "_assistant_handler", False):
            root_logger.removeHandler(handler)
            handler.close()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter(
            "%(levelname)s | %(name)s | %(message)s"
        )
    )
    console_handler._assistant_handler = True

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(JsonFormatter())
    file_handler._assistant_handler = True

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
