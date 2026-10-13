"""Find likely WhatsApp chat rows from discovered UI elements."""

from dataclasses import dataclass

from app.vision.screen_observer import ScreenObserver, UIElementInfo


@dataclass(frozen=True, slots=True)
class ChatCandidate:
    """A likely chat row matching the requested contact."""

    name: str
    control_type: str
    bounds: tuple[int, int, int, int]
    process_id: int


class ChatResultFinder:
    """Identify likely chat rows without performing desktop actions."""

    ROW_TYPES = frozenset({"button", "dataitem", "listitem"})

    def __init__(self, observer: ScreenObserver | None = None) -> None:
        self.observer = observer or ScreenObserver()

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(value.casefold().split())

    def find_candidates(
        self,
        contact_name: str,
        *,
        window_title: str = "WhatsApp",
        max_elements: int = 1000,
    ) -> list[ChatCandidate]:
        """Return likely chat rows containing the requested name."""
        if not isinstance(contact_name, str) or not contact_name.strip():
            raise ValueError("Contact name must not be empty.")

        expected = self._normalize(contact_name)

        elements = self.observer.list_visible_elements(
            window_title=window_title,
            max_elements=max_elements,
        )

        candidates: list[ChatCandidate] = []
        seen: set[tuple[int, int, int, int, int, str]] = set()

        for element in elements:
            if not element.enabled:
                continue

            if element.control_type.casefold() not in self.ROW_TYPES:
                continue

            actual = self._normalize(element.name)
            if expected not in actual:
                continue

            identity = (
                element.process_id,
                element.left,
                element.top,
                element.right,
                element.bottom,
                actual,
            )

            if identity in seen:
                continue

            seen.add(identity)

            candidates.append(
                ChatCandidate(
                    name=element.name,
                    control_type=element.control_type,
                    bounds=(
                        element.left,
                        element.top,
                        element.right,
                        element.bottom,
                    ),
                    process_id=element.process_id,
                )
            )

        return candidates
