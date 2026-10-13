"""Tests for application configuration."""

import pytest

from app.config import load_settings


def test_load_settings_uses_defaults(monkeypatch):
    """Default settings should load successfully."""
    monkeypatch.delenv("ASSISTANT_LOG_LEVEL", raising=False)
    monkeypatch.delenv("ASSISTANT_LOG_FILE", raising=False)
    monkeypatch.delenv("ASSISTANT_DEBUG", raising=False)

    settings = load_settings()

    assert settings.log_level == "INFO"
    assert settings.debug is False
    assert settings.log_file.name == "assistant.log"


def test_load_settings_accepts_debug_mode(monkeypatch):
    """Debug mode should be configurable."""
    monkeypatch.setenv("ASSISTANT_DEBUG", "true")

    assert load_settings().debug is True


def test_load_settings_rejects_invalid_log_level(monkeypatch):
    """Invalid log levels must fail validation."""
    monkeypatch.setenv("ASSISTANT_LOG_LEVEL", "INVALID")

    with pytest.raises(ValueError, match="Invalid ASSISTANT_LOG_LEVEL"):
        load_settings()


def test_load_settings_rejects_invalid_debug_value(monkeypatch):
    """Invalid boolean values must fail validation."""
    monkeypatch.setenv("ASSISTANT_DEBUG", "yes")

    with pytest.raises(ValueError, match="ASSISTANT_DEBUG"):
        load_settings()