"""On-demand Windows desktop observation."""

from dataclasses import dataclass

import pyautogui
from PIL import Image
from pywinauto import Desktop


class ScreenObservationError(Exception):
    """Raised when desktop observation fails."""


@dataclass(frozen=True, slots=True)
class WindowInfo:
    """Public, structured information about a desktop window."""

    title: str
    process_id: int
    visible: bool
    left: int
    top: int
    right: int
    bottom: int


class ScreenObserver:
    """Observe desktop windows and capture screenshots on demand."""

    def list_visible_windows(self) -> list[WindowInfo]:
        """Return visible windows with non-empty titles."""
        try:
            windows = Desktop(backend="uia").windows()
            observations: list[WindowInfo] = []

            for window in windows:
                try:
                    if not window.is_visible():
                        continue

                    title = window.window_text().strip()
                    if not title:
                        continue

                    rect = window.rectangle()

                    observations.append(
                        WindowInfo(
                            title=title,
                            process_id=window.process_id(),
                            visible=True,
                            left=rect.left,
                            top=rect.top,
                            right=rect.right,
                            bottom=rect.bottom,
                        )
                    )

                except Exception:
                    # A window may disappear while being inspected.
                    continue

            return observations

        except Exception as exc:
            raise ScreenObservationError(
                "Could not enumerate Windows desktop windows."
            ) from exc

    def capture_screenshot(self) -> Image.Image:
        """Capture the current screen without saving or logging it."""
        try:
            return pyautogui.screenshot()
        except Exception as exc:
            raise ScreenObservationError(
                "Could not capture the desktop screenshot."
            ) from exc