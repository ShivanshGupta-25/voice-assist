"""Tests for the application entry point."""

import logging

from app.main import main


def test_main_runs_without_error(caplog):
    """The application should log successful initialization."""
    with caplog.at_level(logging.INFO, logger="app.main"):
        main()

    assert "Application initialization started" in caplog.text
    assert "Voice-Controlled AI Desktop Assistant initialized successfully" in (
        caplog.text
    )