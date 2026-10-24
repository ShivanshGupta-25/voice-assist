
"""Find WhatsApp chat results while avoiding duplicate and false matches."""

from __future__ import annotations

from dataclasses import dataclass

from app.vision.screen_observer import ScreenObserver, UIElementInfo


@dataclass(frozen=True, slots=True)
class ChatCandidate:
    """A potential WhatsApp chat row."""

    name: str
    control_type: str
    bounds: tuple[int, int, int, int]
    process_id: int


class ChatResultFinder:
    """Find distinct WhatsApp chat rows matching a contact name."""

    ROW_TYPES = {"dataitem", "listitem", "button"}

    def __init__(
        self,
        observer: ScreenObserver | None = None,
    ) -> None:
        self.observer = observer or ScreenObserver()

    @staticmethod
    def _normalize(value: str) -> str:
        """Normalize capitalization and whitespace."""
        return " ".join(value.casefold().split())

    @classmethod
    def _extract_contact_name(cls, accessible_name: str) -> str:
        """Extract the likely chat title from a WhatsApp row name.

        WhatsApp may expose metadata such as unread counts, timestamps,
        and group descriptions alongside the actual chat title.
        """
        name = " ".join(accessible_name.split())

        # Remove common leading accessibility metadata.
        import re

        name = re.sub(
            r"^\d+\s+unread messages?\s+",
            "",
            name,
            flags=re.IGNORECASE,
        )

        # Individual chats commonly expose a timestamp after the contact
        # name. Group descriptions can contain contact names too, so they
        # must not be treated as exact individual-chat matches.
        name = re.sub(
            r"\s+\d{1,2}:\d{2}\s*(?:am|pm)\b.*$",
            "",
            name,
            flags=re.IGNORECASE,
        )

        return name.strip()

    @classmethod
    def _is_exact_contact_match(
        cls,
        accessible_name: str,
        requested_contact: str,
    ) -> bool:
        """Match the requested contact against the extracted chat title."""
        extracted = cls._normalize(
            cls._extract_contact_name(accessible_name)
        )
        requested = cls._normalize(requested_contact)

        if not extracted or extracted != requested:
            return False

        # Group rows often append group membership or description text.
        # Requiring an exact extracted title prevents those descriptions
        # from being treated as a personal chat.
        return True

    @staticmethod
    def _bounds(
        element: UIElementInfo,
    ) -> tuple[int, int, int, int]:
        """Return the element's screen rectangle."""
        return (
            element.left,
            element.top,
            element.right,
            element.bottom,
        )

    @staticmethod
    def _overlap_ratio(
        first: tuple[int, int, int, int],
        second: tuple[int, int, int, int],
    ) -> float:
        """Calculate intersection area relative to the smaller rectangle."""
        left = max(first[0], second[0])
        top = max(first[1], second[1])
        right = min(first[2], second[2])
        bottom = min(first[3], second[3])

        if right <= left or bottom <= top:
            return 0.0

        intersection = (right - left) * (bottom - top)

        first_area = (first[2] - first[0]) * (first[3] - first[1])
        second_area = (second[2] - second[0]) * (second[3] - second[1])

        smaller_area = min(first_area, second_area)

        if smaller_area <= 0:
            return 0.0

        return intersection / smaller_area

    def find_candidates(
        self,
        contact_name: str,
        *,
        window_title: str = "WhatsApp",
        max_elements: int = 500,
    ) -> list[ChatCandidate]:
        """Return distinct, exact contact-chat candidates.

        Rows that merely mention the contact in a group description are
        excluded. Near-identical UI Automation representations of the same
        row are deduplicated, while distinct matching rows remain ambiguous.
        """
        if not isinstance(contact_name, str) or not contact_name.strip():
            raise ValueError("Contact name must be a non-empty string.")

        requested = self._normalize(contact_name)

        elements = self.observer.list_visible_elements(
            window_title=window_title,
            max_elements=max_elements,
        )

        candidates: list[ChatCandidate] = []

        for element in elements:
            if not element.enabled:
                continue

            if self._normalize(element.control_type) not in self.ROW_TYPES:
                continue

            if not self._is_exact_contact_match(element.name, requested):
                continue

            bounds = self._bounds(element)

            if bounds[2] <= bounds[0] or bounds[3] <= bounds[1]:
                continue

            candidate = ChatCandidate(
                name=element.name,
                control_type=element.control_type,
                bounds=bounds,
                process_id=element.process_id,
            )

            # UI Automation can report the same row multiple times with
            # slightly different rectangles. Collapse only highly overlapping
            # elements from the same process with the same normalized title.
            duplicate_index = None

            for index, existing in enumerate(candidates):
                same_process = existing.process_id == candidate.process_id
                same_name = (
                    self._normalize(
                        self._extract_contact_name(existing.name)
                    )
                    == self._normalize(
                        self._extract_contact_name(candidate.name)
                    )
                )

                overlap = self._overlap_ratio(
                    existing.bounds,
                    candidate.bounds,
                )

                if same_process and same_name and overlap >= 0.85:
                    duplicate_index = index
                    break

            if duplicate_index is None:
                candidates.append(candidate)
            else:
                existing = candidates[duplicate_index]

                # Prefer the larger rectangle, which is more likely to
                # represent the complete clickable chat row.
                existing_area = (
                    (existing.bounds[2] - existing.bounds[0])
                    * (existing.bounds[3] - existing.bounds[1])
                )
                candidate_area = (
                    (candidate.bounds[2] - candidate.bounds[0])
                    * (candidate.bounds[3] - candidate.bounds[1])
                )

                if candidate_area > existing_area:
                    candidates[duplicate_index] = candidate

        return candidates
