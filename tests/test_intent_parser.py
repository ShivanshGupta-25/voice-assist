"""Tests for command normalization and intent parsing."""

import pytest

from app.agent.intent_parser import IntentParser, IntentType


@pytest.fixture
def parser():
    return IntentParser()


@pytest.mark.parametrize(
    ("command", "expected_target"),
    [
        ("Open Notepad", "notepad"),
        ("  launch   Calculator  ", "calculator"),
        ("Please open the Paint.", "paint"),
        ("Start WhatsApp!", "whatsapp"),
    ],
)
def test_parse_launch_commands(parser, command, expected_target):
    """Supported launch phrasing should produce launch intents."""
    intent = parser.parse(command)

    assert intent.kind == IntentType.LAUNCH_APP
    assert intent.target == expected_target


@pytest.mark.parametrize(
    "command",
    ["stop", "Cancel", "cancel task", "abort"],
)
def test_parse_stop_commands(parser, command):
    """Stop commands should produce a stop intent."""
    assert parser.parse(command).kind == IntentType.STOP


def test_parse_unknown_command(parser):
    """Unsupported commands must not be guessed."""
    intent = parser.parse("Send a message to Alex")

    assert intent.kind == IntentType.UNKNOWN
    assert intent.target is None


def test_parse_empty_command(parser):
    """Empty speech results should produce an unknown intent."""
    assert parser.parse("   ").kind == IntentType.UNKNOWN


def test_normalizer_rejects_non_string():
    """Invalid input types should be rejected."""
    from app.agent.command_normalizer import normalize_command

    with pytest.raises(TypeError):
        normalize_command(None)