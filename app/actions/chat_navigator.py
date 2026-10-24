
"""Safely open a uniquely identified WhatsApp chat."""

from dataclasses import dataclass
import time

from app.actions.desktop_controller import (
    DesktopActionError,
    DesktopController,
)
from app.vision.chat_result_finder import (
    ChatCandidate,
    ChatResultFinder,
)
from app.vision.screen_observer import (
    ScreenObservationError,
    ScreenObserver,
)


class ChatNavigationError(RuntimeError):
    """Raised when a chat cannot be opened safely."""


@dataclass(frozen=True, slots=True)
class ChatOpenResult:
    """Describe the outcome of a chat-opening attempt."""

    contact_name: str
    click_position: tuple[int, int]
    verified: bool
    verification_detail: str


class ChatNavigator:
    """Locate and open a uniquely identified WhatsApp chat."""

    def __init__(
        self,
        finder: ChatResultFinder | None = None,
        desktop: DesktopController | None = None,
        observer: ScreenObserver | None = None,
    ) -> None:
        self.observer = observer or ScreenObserver()
        self.finder = finder or ChatResultFinder(observer=self.observer)
        self.desktop = desktop or DesktopController()

    @staticmethod
    def _normalize(value: str) -> str:
        """Normalize text for case-insensitive comparison."""
        return " ".join(value.casefold().split())

    def open_chat(
        self,
        contact_name: str,
        *,
        window_title: str = "WhatsApp",
    ) -> ChatOpenResult:
        """Open one unique matching chat and verify its active header."""
        if not isinstance(contact_name, str) or not contact_name.strip():
            raise ValueError("Contact name must be a non-empty string.")

        requested = contact_name.strip()

        try:
            # Bring the intended application to the foreground.
            self.observer.activate_window(window_title)

            # Refuse to act unless exactly one candidate is found.
            candidates = self.finder.find_candidates(
                requested,
                window_title=window_title,
            )

            if not candidates:
                raise ChatNavigationError(
                    f"No visible WhatsApp chat matched {requested!r}."
                )

            if len(candidates) != 1:
                raise ChatNavigationError(
                    f"Found {len(candidates)} possible chats for "
                    f"{requested!r}; refusing to click."
                )

            candidate: ChatCandidate = candidates[0]

            # Refresh the candidates immediately before clicking.
            refreshed = self.finder.find_candidates(
                requested,
                window_title=window_title,
            )

            if len(refreshed) != 1 or refreshed[0] != candidate:
                raise ChatNavigationError(
                    "WhatsApp results changed during validation. "
                    "Inspect the current screen and retry."
                )

            left, top, right, bottom = candidate.bounds

            if right <= left or bottom <= top:
                raise ChatNavigationError(
                    "The selected contact row has invalid screen bounds."
                )

            x = (left + right) // 2
            y = (top + bottom) // 2

            # Re-activate immediately before the coordinate-based action.
            self.observer.activate_window(window_title)
            self.desktop.click_at(x, y)

            # Allow the interface to update before checking the header.
            time.sleep(0.7)

            self.observer.activate_window(window_title)
            elements = self.observer.list_visible_elements(
                window_title=window_title,
                max_elements=1000,
            )

            expected = self._normalize(requested)

            # Verify the active conversation using its accessible header.
            header_matches = [
                element
                for element in elements
                if element.enabled
                and element.control_type.casefold() == "button"
                and self._normalize(element.name) == expected
                and element.top >= 0
                and element.bottom <= 450
            ]

            if len(header_matches) == 1:
                return ChatOpenResult(
                    contact_name=requested,
                    click_position=(x, y),
                    verified=True,
                    verification_detail=(
                        "The active conversation header matches "
                        "the requested contact name."
                    ),
                )

            return ChatOpenResult(
                contact_name=requested,
                click_position=(x, y),
                verified=False,
                verification_detail=(
                    "Could not uniquely identify the active conversation "
                    "header. Inspect the current UI before continuing."
                ),
            )

        except ChatNavigationError:
            raise
        except (DesktopActionError, ScreenObservationError) as exc:
            raise ChatNavigationError(
                f"Could not safely open chat {requested!r}: {exc}"
            ) from exc
