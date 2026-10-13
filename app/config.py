"""Application configuration and environment settings."""

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable settings for the desktop assistant."""

    app_name: str = "Voice-Controlled AI Desktop Assistant"
    log_level: str = "INFO"
    log_file: Path = PROJECT_ROOT / "logs" / "assistant.log"
    debug: bool = False


def load_settings() -> Settings:
    """Load and validate settings from environment variables."""
    log_level = os.getenv("ASSISTANT_LOG_LEVEL", "INFO").upper()

    allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if log_level not in allowed_levels:
        raise ValueError(
            f"Invalid ASSISTANT_LOG_LEVEL: {log_level}. "
            f"Choose one of: {', '.join(sorted(allowed_levels))}."
        )

    debug_value = os.getenv("ASSISTANT_DEBUG", "false").lower()
    if debug_value not in {"true", "false"}:
        raise ValueError("ASSISTANT_DEBUG must be 'true' or 'false'.")

    return Settings(
        log_level=log_level,
        log_file=Path(
            os.getenv(
                "ASSISTANT_LOG_FILE",
                str(PROJECT_ROOT / "logs" / "assistant.log"),
            )
        ),
        debug=debug_value == "true",
    )