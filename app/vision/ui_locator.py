"""Locate UI controls using accessible names and control types."""

from app.vision.screen_observer import ScreenObserver, UIElementInfo


class UIElementNotFoundError(Exception):
    """Raised when no matching UI element can be found."""


class AmbiguousUIElementError(Exception):
    """Raised when multiple UI elements match a unique lookup."""


class UILocator:
    """Find UI elements without performing desktop interactions."""

    def __init__(self, observer: ScreenObserver | None = None) -> None:
        self.observer = observer or ScreenObserver()

    @staticmethod
    def _normalize(value: str) -> str:
        """Normalize text for case-insensitive matching."""
        return " ".join(value.casefold().split())


    def find_all(
        self,
        name: str,
        *,
        control_type: str | None = None,
        exact: bool = True,
        enabled_only: bool = True,
        window_title: str | None = None,
        max_elements: int = 500,
    ) -> list[UIElementInfo]:
        """Return unique controls matching the supplied criteria.

        Exact matching is the default to reduce accidental matches.
        Set exact=False to search for a name containing the requested text.
        Duplicate entries are removed using the normalized name, control type,
        process ID, and bounding rectangle.
        """
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Element name must be a non-empty string.")

        if control_type is not None and (
            not isinstance(control_type, str) or not control_type.strip()
        ):
            raise ValueError("Control type must be a non-empty string.")

        expected_name = self._normalize(name)
        expected_type = (
            self._normalize(control_type) if control_type else None
        )

        elements = self.observer.list_visible_elements(
            window_title=window_title,
            max_elements=max_elements,
        )

        matches: list[UIElementInfo] = []
        seen: set[tuple[str, str, int, int, int, int, int]] = set()

        for element in elements:
            actual_name = self._normalize(element.name)
            actual_type = self._normalize(element.control_type)

            # Remove duplicate accessibility entries without merging controls
            # that have different process IDs or screen bounds.
            identity = (
                actual_name,
                actual_type,
                element.process_id,
                element.left,
                element.top,
                element.right,
                element.bottom,
            )

            if identity in seen:
                continue

            seen.add(identity)

            if enabled_only and not element.enabled:
                continue

            if expected_type and actual_type != expected_type:
                continue

            if exact:
                name_matches = actual_name == expected_name
            else:
                name_matches = expected_name in actual_name

            if name_matches:
                matches.append(element)

        return matches

    def find_one(
        self,
        name: str,
        *,
        control_type: str | None = None,
        exact: bool = True,
        enabled_only: bool = True,
        window_title: str | None = None,
        max_elements: int = 500,
    ) -> UIElementInfo:
        """Return exactly one match or raise an explicit lookup error."""
        matches = self.find_all(
            name,
            control_type=control_type,
            exact=exact,
            enabled_only=enabled_only,
            window_title=window_title,
            max_elements=max_elements,
        )

        if not matches:
            raise UIElementNotFoundError(
                f"No matching UI element found for {name!r}."
            )

        if len(matches) > 1:
            raise AmbiguousUIElementError(
                f"Found {len(matches)} matching UI elements for {name!r}. "
                "Specify a control type or narrow the window filter."
            )

        return matches[0]
