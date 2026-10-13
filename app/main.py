"""Application entry point for the desktop assistant."""

import logging

from app.config import load_settings
from app.logging_config import configure_logging


def main() -> None:
    """Initialize and start the application."""
    settings = load_settings()

    configure_logging(
        level=settings.log_level,
        log_file=settings.log_file,
    )

    logger = logging.getLogger(__name__)
    logger.info("Application initialization started")
    logger.info("%s initialized successfully", settings.app_name)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as exc:
        logging.basicConfig(level=logging.ERROR)
        logging.getLogger(__name__).error(
            "Application startup failed: %s", exc
        )
        raise SystemExit(1) from exc