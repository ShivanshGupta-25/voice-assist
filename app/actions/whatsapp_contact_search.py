
"""Search for a WhatsApp contact and open a unique matching chat."""

from dataclasses import dataclass

from app.actions.chat_navigator import ChatNavigator, ChatOpenResult
from app.actions.ui_interactor import UIInteractor, UIInteractionError
from app.vision.chat_result_finder import ChatResultFinder


class WhatsAppSearchError(RuntimeError):
    """Raised when contact search cannot proceed safely."""


@dataclass(frozen=True, slots=True)
class ContactSearchResult:
    requested_contact: str
    candidate_count: int
    opened_chat: ChatOpenResult


class WhatsAppContactSearch:
    """Search for a contact and open only a unique matching chat."""

    SEARCH_FIELD = "Search or start a new chat"

    def __init__(
        self,
        interactor: UIInteractor | None = None,
        finder: ChatResultFinder | None = None,
        navigator: ChatNavigator | None = None,
    ) -> None:
        self.interactor = interactor or UIInteractor()
        self.finder = finder or ChatResultFinder()
        self.navigator = navigator or ChatNavigator(finder=self.finder)

    def search_and_open(
        self,
        contact_name: str,
    ) -> ContactSearchResult:
        """Search for a contact, then open one unique result."""
        if not isinstance(contact_name, str) or not contact_name.strip():
            raise ValueError("Contact name must be a non-empty string.")

        requested = contact_name.strip()

        try:
            verified = self.interactor.enter_text_and_verify(
                self.SEARCH_FIELD,
                requested,
                control_type="Edit",
                window_title="WhatsApp",
            )
        except UIInteractionError as exc:
            raise WhatsAppSearchError(
                "Could not safely enter or verify the contact search. "
                "No chat was opened."
            ) from exc

        if not verified:
            raise WhatsAppSearchError(
                "The contact search text could not be verified. "
                "No chat was opened."
            )

        candidates = self.finder.find_candidates(
            requested,
            window_title="WhatsApp",
        )

        if len(candidates) == 0:
            raise WhatsAppSearchError(
                f"No visible result matched {requested!r}. "
                "No chat was opened."
            )

        if len(candidates) > 1:
            raise WhatsAppSearchError(
                f"Found {len(candidates)} possible results for "
                f"{requested!r}. No chat was opened."
            )

        opened = self.navigator.open_chat(requested)

        if not opened.verified:
            raise WhatsAppSearchError(
                "A matching row was clicked, but the active conversation "
                "could not be verified. Stop and inspect WhatsApp."
            )

        return ContactSearchResult(
            requested_contact=requested,
            candidate_count=len(candidates),
            opened_chat=opened,
        )
