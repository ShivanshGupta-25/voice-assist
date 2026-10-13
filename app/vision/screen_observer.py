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


@dataclass(frozen=True, slots=True)
class UIElementInfo:
    """Describes a visible UI element discovered through UI Automation."""

    name: str
    control_type: str
    process_id: int
    enabled: bool
    left: int
    top: int
    right: int
    bottom: int

    @property
    def center(self) -> tuple[int, int]:
        """Return the center point of the element's bounding rectangle."""
        return (
            (self.left + self.right) // 2,
            (self.top + self.bottom) // 2,
        )

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

    def list_visible_elements(
        self,
        window_title: str | None = None,
        max_elements: int = 500,
    ) -> list[UIElementInfo]:
        """Discover visible UI elements without interacting with them.

        Args:
            window_title: Optional case-insensitive substring used to filter
                top-level window titles.
            max_elements: Maximum number of elements returned.

        Returns:
            Visible UI elements with accessible names, types and screen bounds.

        Raises:
            ValueError: If max_elements is not a positive integer.
            ScreenObservationError: If desktop enumeration fails.
        """
        if (
            isinstance(max_elements, bool)
            or not isinstance(max_elements, int)
            or max_elements <= 0
        ):
            raise ValueError("max_elements must be a positive integer.")

        title_filter = (
            window_title.strip().casefold()
            if window_title and window_title.strip()
            else None
        )

        elements: list[UIElementInfo] = []

        try:
            desktop = Desktop(backend="uia")

            for window in desktop.windows():
                if len(elements) >= max_elements:
                    break

                try:
                    if not window.is_visible():
                        continue

                    title = window.window_text().strip()

                    if title_filter and title_filter not in title.casefold():
                        continue

                    for control in window.descendants():
                        if len(elements) >= max_elements:
                            break

                        try:
                            if not control.is_visible():
                                continue

                            rect = control.rectangle()

                            # Ignore elements without usable screen bounds.
                            if rect.right <= rect.left or rect.bottom <= rect.top:
                                continue

                            info = control.element_info

                            name = (
                                info.name
                                or control.window_text()
                                or ""
                            ).strip()

                            control_type = (
                                getattr(info, "control_type", None)
                                or "Unknown"
                            )

                            elements.append(
                                UIElementInfo(
                                    name=name,
                                    control_type=control_type,
                                    process_id=info.process_id,
                                    enabled=control.is_enabled(),
                                    left=rect.left,
                                    top=rect.top,
                                    right=rect.right,
                                    bottom=rect.bottom,
                                )
                            )

                        except Exception:
                            # A stale or inaccessible control should not
                            # prevent discovery of other controls.
                            continue

                except Exception:
                    # Skip individual windows that cannot be inspected.
                    continue

        except Exception as exc:
            raise ScreenObservationError(
                f"Could not enumerate desktop UI elements: {exc}"
            ) from exc

        return elements


    def capture_screenshot(self) -> Image.Image:
        """Capture the current screen without saving or logging it."""
        try:
            return pyautogui.screenshot()
        except Exception as exc:
            raise ScreenObservationError(
                "Could not capture the desktop screenshot."
            ) from exc