"""Tests for accessible UI element lookup."""

from unittest.mock import Mock

import pytest

from app.vision.screen_observer import UIElementInfo
from app.vision.ui_locator import (
    AmbiguousUIElementError,
    UIElementNotFoundError,
    UILocator,
)


def make_element(
    name: str,
    control_type: str = "Edit",
    *,
    enabled: bool = True,
    left: int = 10,
) -> UIElementInfo:
    return UIElementInfo(
        name=name,
        control_type=control_type,
        process_id=1234,
        enabled=enabled,
        left=left,
        top=20,
        right=left + 100,
        bottom=60,
    )


@pytest.fixture
def observer():
    instance = Mock()
    instance.list_visible_elements.return_value = [
        make_element("Search"),
        make_element("Search", "Button", left=150),
        make_element("Search contacts", left=300),
        make_element("Disabled", enabled=False),
    ]
    return instance


def test_find_one_matches_exact_name_and_type(observer):
    locator = UILocator(observer)

    result = locator.find_one("Search", control_type="Edit")

    assert result.name == "Search"
    assert result.control_type == "Edit"
    assert result.center == (60, 40)


def test_find_all_supports_partial_name_matching(observer):
    locator = UILocator(observer)

    results = locator.find_all("search", exact=False)

    assert len(results) == 3


def test_find_all_excludes_disabled_controls_by_default(observer):
    locator = UILocator(observer)

    results = locator.find_all("Disabled")

    assert results == []


def test_find_one_raises_when_no_element_matches(observer):
    locator = UILocator(observer)

    with pytest.raises(UIElementNotFoundError):
        locator.find_one("Missing")


def test_find_one_raises_when_match_is_ambiguous(observer):
    locator = UILocator(observer)

    with pytest.raises(AmbiguousUIElementError):
        locator.find_one("Search")


def test_find_one_rejects_empty_name(observer):
    locator = UILocator(observer)

    with pytest.raises(ValueError):
        locator.find_one("  ")


def test_find_all_passes_window_filter_to_observer(observer):
    locator = UILocator(observer)

    locator.find_all("Search", window_title="WhatsApp")

    observer.list_visible_elements.assert_called_once_with(
        window_title="WhatsApp",
        max_elements=500,
    )
