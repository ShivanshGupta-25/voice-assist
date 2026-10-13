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
