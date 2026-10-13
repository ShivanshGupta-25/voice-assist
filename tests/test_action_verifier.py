"""Tests for observation-based action verification."""

import pytest

from app.verification.action_verifier import ActionVerifier
from app.vision.ocr_reader import TextRegion


def test_verify_text_visible_matches_case_insensitively():
    """Visible text matching should ignore case and extra whitespace."""
    regions = [
        TextRegion(
            text="  Open   WhatsApp ",
            confidence=92,
            left=10,
            top=20,
            width=100,
            height=25,
        )
    ]

    result = ActionVerifier().verify_text_visible(
        "open whatsapp",
        regions,
    )

    assert result.verified is True
    assert result.matched_text == "  Open   WhatsApp "
    assert result.confidence == 92


def test_verify_text_visible_returns_false_without_match():
    """Missing expected text must not be reported as verified."""
    result = ActionVerifier().verify_text_visible(
        "WhatsApp",
        [],
    )

    assert result.verified is False
    assert result.matched_text is None


def test_verify_text_visible_rejects_empty_expectation():
    """An empty expectation cannot be verified."""
    with pytest.raises(ValueError, match="must not be empty"):
        ActionVerifier().verify_text_visible("   ", [])
