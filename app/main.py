"""Application entry point for the desktop assistant."""

import argparse
import logging

from app.actions.desktop_controller import (
    DesktopActionError,
    DesktopController,
)

from app.vision.screen_observer import (
    ScreenObservationError,
    ScreenObserver,
)

from app.config import load_settings
from app.logging_config import configure_logging
from app.voice.speech_input import SpeechInput, SpeechInputError
from app.vision.ocr_reader import OCRReader, OCRReaderError


def main(
    listen: bool = False,
    launch: str | None = None,
    inspect_windows: bool = False,
    capture_screen: bool = False,
    read_screen_text: bool = False,
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

    observer = ScreenObserver()

    if inspect_windows:
        try:
            windows = observer.list_visible_windows()

            if not windows:
                print("No visible titled windows found.")

            for window in windows:
                print(
                    f"Window: {window.title!r} | "
                    f"PID: {window.process_id} | "
                    f"Bounds: ({window.left}, {window.top}, "
                    f"{window.right}, {window.bottom})"
                )

        except ScreenObservationError as exc:
            logger.warning("Window observation failed: %s", exc)
            print(f"Screen observation error: {exc}")

        return

    if capture_screen:
        try:
            screenshot = observer.capture_screenshot()
            print(
                "Screenshot captured in memory: "
                f"{screenshot.width} x {screenshot.height}"
            )
            del screenshot

        except ScreenObservationError as exc:
            logger.warning("Screenshot capture failed: %s", exc)
            print(f"Screen observation error: {exc}")

        return

    if read_screen_text:
        try:
            screenshot = observer.capture_screenshot()
            regions = OCRReader().read_text(screenshot)
            del screenshot

            if not regions:
                print("No readable text detected.")

            for region in regions:
                print(
                    f"Text: {region.text!r} | "
                    f"Confidence: {region.confidence:.1f}% | "
                    f"Bounds: ({region.left}, {region.top}, "
                    f"{region.width}, {region.height})"
                )

        except (ScreenObservationError, OCRReaderError) as exc:
            logger.warning("Screen text recognition failed: %s", exc)
            print(f"Screen text recognition error: {exc}")

        return

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
    operation.add_argument(
        "--inspect-windows",
        action="store_true",
        help="List visible titled desktop windows.",
    )
    operation.add_argument(
        "--capture-screen",
        action="store_true",
        help="Capture a screenshot in memory and report its dimensions.",
    )
    operation.add_argument(
        "--read-screen-text",
        action="store_true",
        help="Capture the screen and recognize visible text using OCR.",
    )

    args = parser.parse_args()

    try:
        main(listen=args.listen,
             launch=args.launch,
             inspect_windows=args.inspect_windows,
             capture_screen=args.capture_screen,
             read_screen_text=args.read_screen_text,
             )
    except (ValueError, OSError) as exc:
        logging.basicConfig(level=logging.ERROR)
        logging.getLogger(__name__).error(
            "Application startup failed: %s",
            exc,
        )
        raise SystemExit(1) from exc