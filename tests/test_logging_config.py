"""Tests for structured application logging."""

import json
import logging

from app.logging_config import configure_logging


def test_logging_writes_json_to_file(tmp_path):
    """Log records should be written as valid JSON."""
    log_file = tmp_path / "logs" / "test.log"
    root_logger = logging.getLogger()
    original_level = root_logger.level

    try:
        configure_logging("INFO", log_file)

        logger = logging.getLogger("test.assistant")
        logger.info("Test event")

        # Flush application-managed handlers before reading the file.
        for handler in root_logger.handlers:
            if getattr(handler, "_assistant_handler", False):
                handler.flush()

        records = log_file.read_text(encoding="utf-8").splitlines()
        assert records

        record = json.loads(records[0])
        assert record["level"] == "INFO"
        assert record["logger"] == "test.assistant"
        assert record["message"] == "Test event"
        assert "timestamp" in record

    finally:
        for handler in root_logger.handlers[:]:
            if getattr(handler, "_assistant_handler", False):
                root_logger.removeHandler(handler)
                handler.close()

        root_logger.setLevel(original_level)
