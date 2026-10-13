"""Tests for guarded UI interaction."""

from unittest.mock import Mock

import pytest

from app.actions.desktop_controller import DesktopActionError
from app.actions.ui_interactor import UIInteractionError, UIInteractor
from app.vision.screen_observer import UIElementInfo
from app.vision.ui_locator import (
    AmbiguousUIElementError,
    UIElementNotFoundError,
)


@pytest.fixture
def element():
    return UIElementInfo(
        name="Search",
        control_type="Edit",
        process_id=1234,
        enabled=True,
        left=100,
        top=200,
        right=300,
        bottom=240,
    )


@pytest.fixture
def locator(element):
    instance = Mock()
    instance.find_one.return_value = element
    return instance


@pytest.fixture
def desktop():
    return Mock()


def test_click_element_uses_element_center(locator, desktop):
    interactor = UIInteractor(locator=locator, desktop=desktop)

    result = interactor.click_element(
        "Search",
        control_type="Edit",
        window_title="WhatsApp",
    )

    assert result == (200, 220)
    desktop.click_at.assert_called_once_with(200, 220)
    locator.find_one.assert_called_once_with(
        "Search",
        control_type="Edit",
        exact=True,
        enabled_only=True,
        window_title="WhatsApp",
    )


def test_click_element_rejects_missing_element(locator, desktop):
    locator.find_one.side_effect = UIElementNotFoundError("Not found")
    interactor = UIInteractor(locator=locator, desktop=desktop)

    with pytest.raises(UIInteractionError):
        interactor.click_element("Missing")

    desktop.click_at.assert_not_called()


def test_click_element_rejects_ambiguous_element(locator, desktop):
    locator.find_one.side_effect = AmbiguousUIElementError("Multiple matches")
    interactor = UIInteractor(locator=locator, desktop=desktop)

    with pytest.raises(UIInteractionError):
        interactor.click_element("Search")

    desktop.click_at.assert_not_called()


def test_click_element_reports_controller_failure(locator, desktop):
    desktop.click_at.side_effect = DesktopActionError("Out of bounds")
    interactor = UIInteractor(locator=locator, desktop=desktop)

    with pytest.raises(UIInteractionError):
        interactor.click_element("Search")

    desktop.click_at.assert_called_once_with(200, 220)


def test_click_element_rejects_invalid_bounds(locator, desktop, element):
    locator.find_one.return_value = UIElementInfo(
        name=element.name,
        control_type=element.control_type,
        process_id=element.process_id,
        enabled=True,
        left=100,
        top=200,
        right=100,
        bottom=240,
    )
    interactor = UIInteractor(locator=locator, desktop=desktop)

    with pytest.raises(UIInteractionError, match="invalid screen bounds"):
        interactor.click_element("Search")

    desktop.click_at.assert_not_called()
