"""Perform guarded interactions with freshly discovered UI elements."""

import logging

from app.actions.desktop_controller import (
    DesktopActionError,
    DesktopController,
)
from app.vision.screen_observer import ScreenObservationError
from app.vision.ui_locator import (
    AmbiguousUIElementError,
    UIElementNotFoundError,
    UILocator,
)

from app.verification.action_verifier import ActionVerifier
from app.vision.ocr_reader import OCRReader, OCRReaderError
from app.vision.screen_observer import ScreenObserver


logger = logging.getLogger(__name__)


class UIInteractionError(Exception):
    """Raised when a UI interaction cannot be performed safely."""


class UIInteractor:
    """Locate and click uniquely identified UI controls."""

    def __init__(
        self,
        locator: UILocator | None = None,
        desktop: DesktopController | None = None,
    ) -> None:
        self.locator = locator or UILocator()
        self.desktop = desktop or DesktopController()

    def enter_text_and_verify(
        self,
        name: str,
        text: str,
        *,
        control_type: str | None = None,
        window_title: str | None = None,
    ) -> bool:
        """Enter text into a located control and verify it with OCR.

        Returns True only when the requested text is detected in the
        post-action screenshot. OCR verification can fail even when the
        text was entered, for example if the text is not currently visible.
        """
        if not isinstance(text, str) or not text or not text.isprintable():
            raise UIInteractionError(
                "Text must be a non-empty, printable string."
            )

        if len(text) > self.desktop.MAX_TEXT_LENGTH:
            raise UIInteractionError(
                f"Text cannot exceed {self.desktop.MAX_TEXT_LENGTH} characters."
            )

        # Re-discover the target immediately before interacting.
        self.click_element(
            name,
            control_type=control_type,
            window_title=window_title,
        )

        try:
            self.desktop.type_text(text)

            observer = self.locator.observer
            screenshot = observer.capture_screenshot()
            regions = OCRReader().read_text(screenshot)

            result = ActionVerifier().verify_text_visible(text, regions)

            if not result.verified:
                raise UIInteractionError(
                    "Text entry was attempted, but OCR could not verify "
                    "the requested text on screen."
                )

            logger.info("Text entry verified by OCR.")
            return True

        except UIInteractionError:
            raise
        except (DesktopActionError, ScreenObservationError, OCRReaderError) as exc:
            raise UIInteractionError(
                f"Text entry or verification failed: {exc}"
            ) from exc


    def click_element(
        self,
        name: str,
        *,
        control_type: str | None = None,
        window_title: str | None = None,
        exact: bool = True,
    ) -> tuple[int, int]:
        """Find a control, validate its bounds, and click its current center.

        The control is looked up immediately before the click. Ambiguous
        matches are rejected rather than selecting the first match.
        """
        try:
            element = self.locator.find_one(
                name,
                control_type=control_type,
                exact=exact,
                enabled_only=True,
                window_title=window_title,
            )

            # Validate the discovered rectangle before using its center.
            if (
                element.right <= element.left
                or element.bottom <= element.top
            ):
                raise UIInteractionError(
                    "The selected UI element has invalid screen bounds."
                )

            x, y = element.center

            logger.info(
                "Clicking discovered UI element: name=%r type=%s",
                element.name,
                element.control_type,
            )

            self.desktop.click_at(x, y)
            return x, y

        except (
            UIElementNotFoundError,
            AmbiguousUIElementError,
            ScreenObservationError,
            DesktopActionError,
        ) as exc:
            raise UIInteractionError(
                f"Could not safely click UI element {name!r}: {exc}"
            ) from exc
