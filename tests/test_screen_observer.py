"""Tests for on-demand screen observation."""

from types import SimpleNamespace

import pytest

from app.vision.screen_observer import (
    ScreenObservationError,
    ScreenObserver,
)


def test_list_visible_windows_returns_structured_data(monkeypatch):
    """Visible windows should be represented as structured observations."""

    class FakeWindow:
        def is_visible(self):
            return True

        def window_text(self):
            return "Notepad"

        def process_id(self):
            return 1234

        def rectangle(self):
            return SimpleNamespace(
                left=10,
                top=20,
                right=810,
                bottom=620,
            )

    class FakeDesktop:
        def __init__(self, backend):
            assert backend == "uia"

        def windows(self):
            return [FakeWindow()]

    monkeypatch.setattr(
        "app.vision.screen_observer.Desktop",
        FakeDesktop,
    )

    windows = ScreenObserver().list_visible_windows()

    assert len(windows) == 1
    assert windows[0].title == "Notepad"
    assert windows[0].process_id == 1234
    assert windows[0].visible is True
    assert windows[0].left == 10
    assert windows[0].bottom == 620


def test_list_visible_windows_ignores_invisible_windows(monkeypatch):
    """Invisible windows should not appear in observations."""

    class FakeWindow:
        def is_visible(self):
            return False

    class FakeDesktop:
        def __init__(self, backend):
            pass

        def windows(self):
            return [FakeWindow()]

    monkeypatch.setattr(
        "app.vision.screen_observer.Desktop",
        FakeDesktop,
    )

    assert ScreenObserver().list_visible_windows() == []


def test_list_visible_windows_wraps_enumeration_errors(monkeypatch):
    """Enumeration failures should raise a controlled error."""

    class FakeDesktop:
        def __init__(self, backend):
            pass

        def windows(self):
            raise OSError("Desktop unavailable")

    monkeypatch.setattr(
        "app.vision.screen_observer.Desktop",
        FakeDesktop,
    )

    with pytest.raises(
        ScreenObservationError,
        match="Could not enumerate",
    ):
        ScreenObserver().list_visible_windows()


def test_capture_screenshot_is_on_demand(monkeypatch):
    """Screenshot capture should return an image without saving it."""
    expected_image = object()

    monkeypatch.setattr(
        "app.vision.screen_observer.pyautogui.screenshot",
        lambda: expected_image,
    )

    result = ScreenObserver().capture_screenshot()

    assert result is expected_image


def test_capture_screenshot_wraps_errors(monkeypatch):
    """Screenshot failures should be reported consistently."""

    def fail_capture():
        raise OSError("Capture failed")

    monkeypatch.setattr(
        "app.vision.screen_observer.pyautogui.screenshot",
        fail_capture,
    )

    with pytest.raises(
        ScreenObservationError,
        match="Could not capture",
    ):
        ScreenObserver().capture_screenshot()