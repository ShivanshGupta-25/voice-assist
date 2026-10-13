"""Safe, bounded desktop actions for Windows."""

import os
import subprocess
from typing import Final

import pyautogui

from app.actions.action_registry import ALLOWED_APPS

class DesktopActionError(Exception):
    """Raised when a desktop action is invalid or fails."""


class DesktopController:
    """Execute explicitly requested, allowlisted desktop actions."""

    # Only these applications may be launched through this controller.
    # ALLOWED_APPS: Final[dict[str, str]] = {
    #     "notepad": "notepad.exe",
    #     "calculator": "calc.exe",
    #     "paint": "mspaint.exe",
    #     "whatsapp": "whatsapp:",
    # }
    ALLOWED_APPS = ALLOWED_APPS

    # Limit the keys accepted by the basic keyboard interface.
    ALLOWED_KEYS: Final[frozenset[str]] = frozenset({
        "enter",
        "esc",
        "tab",
        "space",
        "backspace",
        "delete",
        "up",
        "down",
        "left",
        "right",
        "home",
        "end",
        "pageup",
        "pagedown",
    })

    MAX_TEXT_LENGTH: Final[int] = 300

    def __init__(self) -> None:
        """Enable PyAutoGUI's fail-safe and action delay."""
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1

    def launch_app(self, app_name: str) -> str:
        """Launch an approved application without using a shell."""
        name = app_name.strip().lower()

        if name not in self.ALLOWED_APPS:
            allowed = ", ".join(sorted(self.ALLOWED_APPS))
            raise DesktopActionError(
                f"Application '{name}' is not allowed. "
                f"Allowed applications: {allowed}."
            )

        target = self.ALLOWED_APPS[name]

        try:
            if name == "whatsapp":
                # Windows must have a registered WhatsApp URI handler.
                startfile = getattr(os, "startfile", None)
                if startfile is None:
                    raise DesktopActionError(
                        "WhatsApp URI launching is supported on Windows only."
                    )
                startfile(target)
            else:
                subprocess.Popen([target], shell=False)

        except DesktopActionError:
            raise
        except OSError as exc:
            raise DesktopActionError(
                f"Could not launch {name}: {exc}"
            ) from exc

        return name

    def press_key(self, key: str) -> None:
        """Press one approved keyboard key."""
        normalized_key = key.strip().lower()

        if normalized_key not in self.ALLOWED_KEYS:
            raise DesktopActionError(
                f"Key '{normalized_key}' is not allowed."
            )

        try:
            pyautogui.press(normalized_key)
        except pyautogui.FailSafeException:
            raise
        except Exception as exc:
            raise DesktopActionError(
                f"Could not press key '{normalized_key}'."
            ) from exc

    def type_text(self, text: str) -> None:
        """Type a short, printable string into the focused application."""
        if not isinstance(text, str) or not text:
            raise DesktopActionError("Text must not be empty.")

        if len(text) > self.MAX_TEXT_LENGTH:
            raise DesktopActionError(
                f"Text cannot exceed {self.MAX_TEXT_LENGTH} characters."
            )

        if not text.isprintable():
            raise DesktopActionError(
                "Text cannot contain control characters or newlines."
            )

        try:
            pyautogui.write(text, interval=0.02)
        except pyautogui.FailSafeException:
            raise
        except Exception as exc:
            raise DesktopActionError("Could not type the requested text.") from exc

    def click_at(self, x: int, y: int) -> None:
        """Click explicitly supplied screen coordinates within screen bounds."""
        # Reject booleans as well as non-integer coordinates.
        if (
            isinstance(x, bool)
            or isinstance(y, bool)
            or not isinstance(x, int)
            or not isinstance(y, int)
        ):
            raise DesktopActionError("Click coordinates must be integers.")

        width, height = pyautogui.size()

        if not (0 <= x < width and 0 <= y < height):
            raise DesktopActionError(
                f"Coordinates ({x}, {y}) are outside the screen bounds "
                f"({width} x {height})."
            )

        try:
            pyautogui.click(x=x, y=y)
        except pyautogui.FailSafeException:
            raise
        except Exception as exc:
            raise DesktopActionError(
                f"Could not click at ({x}, {y})."
            ) from exc