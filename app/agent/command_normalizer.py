"""Normalize recognized speech before intent parsing."""


def normalize_command(command: str) -> str:
    """Normalize whitespace and casing without changing command meaning."""
    if not isinstance(command, str):
        raise TypeError("Command must be a string.")

    return " ".join(command.casefold().strip().split())