
"""Convert normalized commands into structured intents."""

import re
from dataclasses import dataclass
from enum import Enum

from app.agent.command_normalizer import normalize_command


class IntentType(str, Enum):
    """Supported high-level command intents."""

    LAUNCH_APP = "launch_app"
    OPEN_WHATSAPP_CHAT = "open_whatsapp_chat"
    STOP = "stop"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Intent:
    """Structured interpretation of a recognized command."""

    kind: IntentType
    raw_command: str
    target: str | None = None


class IntentParser:
    """Parse a deliberately limited set of desktop commands."""

    _LAUNCH_PATTERN = re.compile(
        r"^(?:please\s+)?(?:open|launch|start|run)\s+"
        r"(?P<target>[\w][\w -]*?)[.!?]*$"
    )

    _WHATSAPP_CHAT_PATTERN = re.compile(
        r"^(?:please\s+)?open\s+whatsapp\s+and\s+"
        r"(?:open|show)\s+"
        r"(?P<contact>.+?)\s+chat[.!?]*$"
    )

    _STOP_COMMANDS = {
        "stop",
        "cancel",
        "cancel task",
        "stop assistant",
        "abort",
    }

    def parse(self, command: str) -> Intent:
        """Parse a command without executing any action."""
        if not isinstance(command, str):
            return Intent(
                kind=IntentType.UNKNOWN,
                raw_command="",
            )

        normalized = normalize_command(command)

        if not normalized:
            return Intent(
                kind=IntentType.UNKNOWN,
                raw_command=command,
            )

        if normalized in self._STOP_COMMANDS:
            return Intent(
                kind=IntentType.STOP,
                raw_command=command,
            )

        # Match a request to open a specific WhatsApp contact.
        chat_match = self._WHATSAPP_CHAT_PATTERN.fullmatch(normalized)

        if chat_match:
            contact = chat_match.group("contact").strip()

            # Remove a possessive suffix, e.g. "Sweta Koshta's chat".
            if contact.endswith(("'s", "’s")):
                contact = contact[:-2].strip()

            if contact:
                return Intent(
                    kind=IntentType.OPEN_WHATSAPP_CHAT,
                    raw_command=command,
                    target=contact,
                )

            return Intent(
                kind=IntentType.UNKNOWN,
                raw_command=command,
            )

        # Preserve existing application-launch behavior.
        match = self._LAUNCH_PATTERN.fullmatch(normalized)

        if match:
            target = match.group("target").strip()

            if target.startswith("the "):
                target = target[4:].strip()

            return Intent(
                kind=IntentType.LAUNCH_APP,
                raw_command=command,
                target=target,
            )

        return Intent(
            kind=IntentType.UNKNOWN,
            raw_command=command,
        )
