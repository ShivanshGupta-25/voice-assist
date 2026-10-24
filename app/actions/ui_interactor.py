
"""Perform guarded interactions with freshly discovered UI elements."""

from __future__ import annotations

import logging
import time

from pywinauto import Desktop

from app.actions.desktop_controller import (
    DesktopActionError,
    DesktopController,
)
from app.vision.ocr_reader import OCRReader, OCRReaderError
from app.vision.screen_observer import ScreenObservationError
from app.vision.ui_locator import (
    AmbiguousUIElementError,
    UIElementNotFoundError,
    UILocator,
)
from app.verification.action_verifier import ActionVerifier


logger = logging.getLogger(__name__)

# Short delay to allow the UI Automation provider to update its value.
UI_VALUE_REFRESH_DELAY = 0.2


class UIInteractionError(RuntimeError):
    """Raised when a UI interaction cannot be performed safely."""


class UIInteractor:
    """Locate and interact with uniquely identified UI controls."""

    def __init__(
        self,
        locator: UILocator | None = None,
        desktop: DesktopController | None = None,
    ) -> None:
        self.locator = locator or UILocator()
        self.desktop = desktop or DesktopController()

    @staticmethod
    def _normalize(value: str) -> str:
        """Normalize whitespace and capitalization for comparisons."""
        return " ".join(value.casefold().split())

    def _activate_window(self, window_title: str | None) -> None:
        """Activate the requested window when a title is provided."""
        if not window_title:
            return

        try:
            self.locator.observer.activate_window(window_title)
        except (ScreenObservationError, ValueError) as exc:
            raise UIInteractionError(
                f"Could not activate window {window_title!r}. "
                "No interaction was performed."
            ) from exc

    @staticmethod
    def _read_edit_value_at(
        x: int,
        y: int,
        window_title: str,
    ) -> str | None:
        """Read the focused Edit control at the original click position.

        The accessible name of an Edit control can change or become empty
        after typing. Therefore, identify the field using its screen bounds
        and keyboard focus rather than relying on its accessible name.
        """
        try:
            window = Desktop(backend="uia").window(title=window_title)

            if not window.exists(timeout=1):
                return None

            for element in window.descendants(control_type="Edit"):
                try:
                    if not element.is_enabled():
                        continue

                    if not element.has_keyboard_focus():
                        continue

                    rect = element.rectangle()

                    # The field can resize after text entry, so check whether
                    # the original click position remains inside its bounds.
                    if not (
                        rect.left <= x <= rect.right
                        and rect.top <= y <= rect.bottom
                    ):
                        continue

                    value = element.get_value()
                    return value if isinstance(value, str) else None

                except Exception:
                    # A UIA element can disappear or become stale while the
                    # application updates its controls.
                    continue

        except Exception:
            logger.debug(
                "Could not read the focused Edit control through UIA.",
                exc_info=True,
            )

        return None

    def enter_text_and_verify(
        self,
        name: str,
        text: str,
        *,
        control_type: str | None = None,
        window_title: str | None = None,
    ) -> bool:
        """Enter text and verify it using UI Automation, then OCR if needed.

        UI Automation is preferred because OCR may not reliably recognize
        text inside a focused input field. OCR is used when UIA cannot expose
        the value of the targeted field.

        Returns:
            True only when the entered text can be verified.

        Raises:
            UIInteractionError: If input or verification fails.
        """
        if not isinstance(text, str) or not text or not text.isprintable():
            raise UIInteractionError(
                "Text must be a non-empty, printable string."
            )

        if len(text) > self.desktop.MAX_TEXT_LENGTH:
            raise UIInteractionError(
                f"Text cannot exceed "
                f"{self.desktop.MAX_TEXT_LENGTH} characters."
            )

        # Activate the target application before locating its controls.
        self._activate_window(window_title)

        # Locate the target and click it. Keep the click coordinates because
        # the Edit control's accessible name may change after typing.
        x, y = self.click_element(
            name,
            control_type=control_type,
            window_title=window_title,
        )

        try:
            # Replace the existing field contents.
            self.desktop.press_shortcut("ctrl+a")
            self.desktop.press_key("backspace")
            self.desktop.type_text(text)

            # Allow UI Automation time to expose the updated value.
            time.sleep(UI_VALUE_REFRESH_DELAY)

            # Prefer reading the value from the exact focused field.
            if window_title:
                field_value = self._read_edit_value_at(x, y, window_title)

                if field_value is not None:
                    if self._normalize(field_value) == self._normalize(text):
                        logger.info(
                            "Text entry verified through UI Automation."
                        )
                        return True

                    logger.warning(
                        "UI Automation returned a value that did not match "
                        "the requested text."
                    )
                    raise UIInteractionError(
                        "The target field's current value does not match "
                        "the requested text. Verification failed."
                    )

            # UIA did not expose the target field's value. Fall back to OCR.
            observer = self.locator.observer

            if window_title:
                screenshot = observer.capture_window_screenshot(window_title)
            else:
                screenshot = observer.capture_screenshot()

            regions = OCRReader().read_text(screenshot)
            verification = ActionVerifier().verify_text_visible(text, regions)

            combined_ocr_text = " ".join(
                region.text.strip()
                for region in regions
                if region.text.strip()
            )

            expected = self._normalize(text)
            recognized = self._normalize(combined_ocr_text)

            verified = verification.verified or expected in recognized

            if not verified:
                logger.warning(
                    "Text verification failed. Requested text: %r",
                    text,
                )
                logger.debug(
                    "OCR detected regions: %s",
                    [region.text for region in regions],
                )
                raise UIInteractionError(
                    "Text entry was attempted, but neither UI Automation "
                    "nor OCR could verify the requested text."
                )

            logger.info("Text entry verified through OCR.")
            return True

        except UIInteractionError:
            raise
        except (
            DesktopActionError,
            ScreenObservationError,
            OCRReaderError,
        ) as exc:
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
        """Find a control, validate its bounds, and click its center.

        Ambiguous matches are rejected rather than selecting an arbitrary
        element.
        """
        self._activate_window(window_title)

        try:
            element = self.locator.find_one(
                name,
                control_type=control_type,
                exact=exact,
                enabled_only=True,
                window_title=window_title,
            )

            # Reject invalid or zero-sized rectangles.
            if (
                element.right <= element.left
                or element.bottom <= element.top
            ):
                raise UIInteractionError(
                    "The selected UI element has invalid screen bounds."
                )

            x, y = element.center

            logger.info(
                "Clicking UI element: name=%r, type=%s, bounds=(%s, %s, %s, %s)",
                element.name,
                element.control_type,
                element.left,
                element.top,
                element.right,
                element.bottom,
            )

            self.desktop.click_at(x, y)
            return x, y

        except UIInteractionError:
            raise
        except (
            UIElementNotFoundError,
            AmbiguousUIElementError,
            ScreenObservationError,
            DesktopActionError,
        ) as exc:
            raise UIInteractionError(
                f"Could not safely click UI element {name!r}: {exc}"
            ) from exc
