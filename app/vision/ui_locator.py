
"""Locate UI controls by accessible name and control type.

This module provides safe, reusable lookup methods for visible UI elements.
It does not perform any desktop interactions.
"""

from __future__ import annotations

from app.vision.screen_observer import ScreenObserver, UIElementInfo


class UIElementNotFoundError(RuntimeError):
    """Raised when no matching UI element can be found."""


class AmbiguousUIElementError(RuntimeError):
    """Raised when multiple elements match a supposedly unique lookup."""


class UILocator:
    """Find visible UI elements using their accessible properties."""

    def __init__(
        self,
        observer: ScreenObserver | None = None,
    ) -> None:
        self.observer = observer or ScreenObserver()

    @staticmethod
    def _normalize(value: str) -> str:
        """Normalize whitespace and capitalization for comparisons."""
        return " ".join(value.casefold().split())

    def find_all(
        self,
        name: str,
        *,
        control_type: str | None = None,
        window_title: str | None = None,
        exact: bool = True,
        enabled_only: bool = True,
        max_elements: int = 500,
    ) -> list[UIElementInfo]:
        """Return all visible elements matching the supplied criteria.

        Args:
            name: Accessible name or text to search for.
            control_type: Optional UI Automation control type, such as
                ``Button`` or ``Edit``.
            window_title: Optional title of the target window.
            exact: If True, require an exact normalized name match.
                Otherwise, allow the requested name to appear within it.
            enabled_only: If True, exclude disabled controls.
            max_elements: Maximum number of UI elements to inspect.

        Returns:
            Matching UI elements, with duplicate observations removed.

        Raises:
            ValueError: If the lookup arguments are invalid.
        """
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Element name must be a non-empty string.")

        if control_type is not None:
            if not isinstance(control_type, str) or not control_type.strip():
                raise ValueError(
                    "control_type must be a non-empty string or None."
                )

        if not isinstance(max_elements, int) or isinstance(max_elements, bool):
            raise ValueError("max_elements must be a positive integer.")

        if max_elements <= 0:
            raise ValueError("max_elements must be a positive integer.")

        expected_name = self._normalize(name)
        expected_type = (
            self._normalize(control_type)
            if control_type is not None
            else None
        )

        elements = self.observer.list_visible_elements(
            window_title=window_title,
            max_elements=max_elements,
        )

        matches: list[UIElementInfo] = []
        seen: set[tuple] = set()

        for element in elements:
            element_name = self._normalize(element.name)
            element_type = self._normalize(element.control_type)

            # Ignore controls without accessible names.
            if not element_name:
                continue

            # Optionally exclude controls that cannot be interacted with.
            if enabled_only and not element.enabled:
                continue

            # Match the requested control type when one was specified.
            if expected_type is not None and element_type != expected_type:
                continue

            # Match the accessible name.
            if exact:
                name_matches = element_name == expected_name
            else:
                name_matches = expected_name in element_name

            if not name_matches:
                continue

            # Remove duplicate observations of the same UI element.
            bounds = (
                element.left,
                element.top,
                element.right,
                element.bottom,
            )

            identity = (
                element_name,
                element_type,
                element.process_id,
                bounds,
            )

            if identity in seen:
                continue

            seen.add(identity)
            matches.append(element)

        return matches

    def find_one(
        self,
        name: str,
        *,
        control_type: str | None = None,
        window_title: str | None = None,
        exact: bool = True,
        enabled_only: bool = True,
        max_elements: int = 500,
    ) -> UIElementInfo:
        """Return exactly one matching UI element.

        Raises:
            UIElementNotFoundError: If no matching element exists.
            AmbiguousUIElementError: If multiple elements match.
        """
        matches = self.find_all(
            name,
            control_type=control_type,
            window_title=window_title,
            exact=exact,
            enabled_only=enabled_only,
            max_elements=max_elements,
        )

        if not matches:
            raise UIElementNotFoundError(
                f"No UI element matched name={name!r}, "
                f"control_type={control_type!r}, "
                f"window_title={window_title!r}."
            )

        if len(matches) > 1:
            descriptions = [
                (
                    f"name={element.name!r}, "
                    f"type={element.control_type!r}, "
                    f"bounds=({element.left}, {element.top}, "
                    f"{element.right}, {element.bottom})"
                )
                for element in matches[:5]
            ]

            details = "; ".join(descriptions)

            raise AmbiguousUIElementError(
                f"Found {len(matches)} UI elements matching "
                f"name={name!r}. Refusing to select one arbitrarily. "
                f"Matches: {details}"
            )

        return matches[0]
