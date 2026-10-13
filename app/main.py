"""Application entry point for the desktop assistant."""

import argparse
import logging

from app.actions.desktop_controller import (
    DesktopActionError,
    DesktopController,
)
from app.config import load_settings
from app.logging_config import configure_logging
from app.voice.speech_input import SpeechInput, SpeechInputError


def main(
    listen: bool = False,
    launch: str | None = None,
) -> None:
    """Initialize the app and run one explicitly requested operation."""
    settings = load_settings()

    configure_logging(
        level=settings.log_level,
        log_file=settings.log_file,
    )

    logger = logging.getLogger(__name__)
    logger.info("Application initialization started")
    logger.info("%s initialized successfully", settings.app_name)

    if launch is not None:
        try:
            app_name = DesktopController().launch_app(launch)
            logger.info("Launch request dispatched for %s", app_name)
            print(f"Launch request sent: {app_name}")

        except DesktopActionError as exc:
            logger.warning("Desktop action failed: %s", exc)
            print(f"Desktop action error: {exc}")

        return

    if listen:
        try:
            command = SpeechInput().listen_once()
            print(f"\nRecognized command: {command}")

        except (SpeechInputError, OSError) as exc:
            logger.warning("Voice input failed: %s", exc)
            print(f"\nVoice input error: {exc}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Voice-Controlled AI Desktop Assistant"
    )

    operation = parser.add_mutually_exclusive_group()
    operation.add_argument(
        "--listen",
        action="store_true",
        help="Capture and transcribe one spoken command.",
    )
    operation.add_argument(
        "--launch",
        metavar="APP",
        help="Launch an approved application, such as notepad.",
    )

    args = parser.parse_args()

    try:
        main(listen=args.listen, launch=args.launch)
    except (ValueError, OSError) as exc:
        logging.basicConfig(level=logging.ERROR)
        logging.getLogger(__name__).error(
            "Application startup failed: %s",
            exc,
        )
        raise SystemExit(1) from exc