"""Tests for safe desktop actions."""

import pytest

from app.actions.desktop_controller import (
    DesktopActionError,
    DesktopController,
)


@pytest.fixture
def controller():
    return DesktopController()


def test_launch_app_allows_notepad(controller, monkeypatch):
    """Approved applications should launch without a shell."""
    calls = []

    def fake_popen(args, shell):
        calls.append((args, shell))

    monkeypatch.setattr(
        "app.actions.desktop_controller.subprocess.Popen",
        fake_popen,
    )

    result = controller.launch_app("Notepad")

    assert result == "notepad"
    assert calls == [(["notepad.exe"], False)]


def test_launch_app_rejects_unknown_application(controller):
    """Unapproved applications must not be launched."""
    with pytest.raises(DesktopActionError, match="not allowed"):
        controller.launch_app("unknown-app")


def test_press_key_rejects_unapproved_key(controller, monkeypatch):
    """The keyboard interface must enforce its key allowlist."""
    monkeypatch.setattr(
        "app.actions.desktop_controller.pyautogui.press",
        lambda key: pytest.fail("No key should be pressed"),
    )

    with pytest.raises(DesktopActionError, match="not allowed"):
        controller.press_key("f12")


def test_type_text_rejects_newlines(controller, monkeypatch):
    """Multiline text should be rejected by the basic typing interface."""
    monkeypatch.setattr(
        "app.actions.desktop_controller.pyautogui.write",
        lambda *args, **kwargs: pytest.fail("Text should not be typed"),
    )

    with pytest.raises(DesktopActionError, match="control characters"):
        controller.type_text("first line\nsecond line")


def test_type_text_rejects_oversized_input(controller):
    """Typing should be limited to a bounded input length."""
    with pytest.raises(DesktopActionError, match="cannot exceed"):
        controller.type_text("a" * 301)


def test_click_rejects_out_of_bounds_coordinates(controller, monkeypatch):
    """Clicks outside the screen must be rejected."""
    monkeypatch.setattr(
        "app.actions.desktop_controller.pyautogui.size",
        lambda: (1920, 1080),
    )
    monkeypatch.setattr(
        "app.actions.desktop_controller.pyautogui.click",
        lambda **kwargs: pytest.fail("No click should occur"),
    )

    with pytest.raises(DesktopActionError, match="outside the screen"):
        controller.click_at(1920, 1080)