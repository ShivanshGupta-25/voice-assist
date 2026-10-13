"""Convert normalized commands into structured intents."""

import re
from dataclasses import dataclass
from enum import Enum

from app.agent.command_normalizer import normalize_command


class IntentType(str, Enum):
    """Supported high-level command intents."""

    LAUNCH_APP = "launch_app"
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

    _STOP_COMMANDS = {
        "stop",
        "cancel",
        "cancel task",
        "stop assistant",
        "abort",
    }

    def parse(self, command: str) -> Intent:
        """Parse a command without executing any action."""
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

        match = self._LAUNCH_PATTERN.fullmatch(normalized)

        if match:
            target = match.group("target").strip()

            # Remove a leading article without guessing the application.
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