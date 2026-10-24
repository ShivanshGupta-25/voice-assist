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

from app.agent.intent_parser import IntentParser
from app.agent.task_planner import PlanningError, TaskPlanner

from app.agent.task_executor import TaskExecutor, TaskExecutionError

def main(
    listen: bool = False,
    launch: str | None = None,
    inspect_windows: bool = False,
    capture_screen: bool = False,
    read_screen_text: bool = False,
    plan_command: str | None = None,
    execute_command: str | None = None,
    inspect_controls: str | None = None,
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


    if inspect_controls is not None:
        try:
            title_filter = inspect_controls or None

            elements = observer.list_visible_elements(
                window_title=title_filter,
                max_elements=500,
            )

            if not elements:
                print("No visible UI elements found.")

            for index, element in enumerate(elements, start=1):
                print(
                    f"{index}. Name: {element.name!r} | "
                    f"Type: {element.control_type} | "
                    f"PID: {element.process_id} | "
                    f"Enabled: {element.enabled} | "
                    f"Bounds: ({element.left}, {element.top}, "
                    f"{element.right}, {element.bottom}) | "
                    f"Center: {element.center}"
                )

            print(f"\nDiscovered {len(elements)} UI elements.")

        except (ScreenObservationError, ValueError) as exc:
            logger.warning("UI element discovery failed: %s", exc)
            print(f"UI inspection error: {exc}")

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

    if plan_command is not None:
        try:
            intent = IntentParser().parse(plan_command)
            plan = TaskPlanner().plan(intent)

        except PlanningError as exc:
            print(f"Planning error: {exc}")
            return

        if plan.stop_requested:
            print("Stop requested. No actions planned.")
            return

        print("Validated task plan:")

        for index, action in enumerate(plan.actions, start=1):
            print(
                f"{index}. Action: {action.action} | "
                f"Target: {action.target}"
            )

        return


    if execute_command is not None:
        try:
            intent = IntentParser().parse(execute_command)
            plan = TaskPlanner().plan(intent)
            results = TaskExecutor().execute(plan)

            for result in results:
                print(result)

        except (PlanningError, TaskExecutionError) as exc:
            logger.warning("Command execution failed: %s", exc)
            print(f"Execution error: {exc}")

        return

    # Default operation: listen for and execute one command.
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
    operation.add_argument(
        "--plan",
        metavar="COMMAND",
        help="Parse and plan a command without executing it.",
    )
    operation.add_argument(
        "--execute",
        metavar="COMMAND",
        help="Validate and execute a supported command.",
    )
    operation.add_argument(
        "--inspect-controls",
        nargs="?",
        const="",
        metavar="WINDOW",
        help=(
            "Inspect visible UI controls, optionally filtered by "
            "a window-title substring."
        ),
    )

    args = parser.parse_args()

    try:
        main(listen=args.listen,
             launch=args.launch,
             inspect_windows=args.inspect_windows,
             capture_screen=args.capture_screen,
             read_screen_text=args.read_screen_text,
             plan_command=args.plan,
             execute_command=args.execute,
             inspect_controls=args.inspect_controls,
             )
    except (ValueError, OSError) as exc:
        logging.basicConfig(level=logging.ERROR)
        logging.getLogger(__name__).error(
            "Application startup failed: %s",
            exc,
        )
        raise SystemExit(1) from exc