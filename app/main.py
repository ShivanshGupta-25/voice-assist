"""Application entry point for the desktop assistant."""

import argparse
import logging

from app.config import load_settings
from app.logging_config import configure_logging
from app.voice.speech_input import SpeechInput, SpeechInputError


def main(listen: bool = False) -> None:
    """Initialize the application and optionally capture a command."""
    settings = load_settings()

    configure_logging(
        level=settings.log_level,
        log_file=settings.log_file,
    )

    logger = logging.getLogger(__name__)
    logger.info("Application initialization started")
    logger.info("%s initialized successfully", settings.app_name)

    if not listen:
        return

    try:
        speech_input = SpeechInput()
        command = speech_input.listen_once()
        print(f"\nRecognized command: {command}")

    except (SpeechInputError, OSError) as exc:
        logger.warning("Voice input failed: %s", exc)
        print(f"\nVoice input error: {exc}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Voice-Controlled AI Desktop Assistant"
    )
    parser.add_argument(
        "--listen",
        action="store_true",
        help="Capture and transcribe one spoken command.",
    )
    args = parser.parse_args()

    try:
        main(listen=args.listen)
    except (ValueError, OSError) as exc:
        logging.basicConfig(level=logging.ERROR)
        logging.getLogger(__name__).error(
            "Application startup failed: %s",
            exc,
        )
        raise SystemExit(1) from exc
