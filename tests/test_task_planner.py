"""Tests for safe task planning."""

import pytest

from app.agent.intent_parser import IntentParser, IntentType
from app.agent.task_planner import PlanningError, TaskPlanner


@pytest.fixture
def planner():
    return TaskPlanner()


def test_plan_launch_app(planner):
    """An allowlisted launch intent should produce one action."""
    intent = IntentParser().parse("Open Notepad")
    plan = planner.plan(intent)

    assert plan.stop_requested is False
    assert len(plan.actions) == 1
    assert plan.actions[0].action == "launch_app"
    assert plan.actions[0].target == "notepad"


def test_plan_rejects_unapproved_application(planner):
    """Unsupported applications must fail closed."""
    intent = IntentParser().parse("Open a browser")

    with pytest.raises(PlanningError, match="not allowed"):
        planner.plan(intent)


def test_plan_rejects_unknown_intent(planner):
    """Unknown commands must not produce executable actions."""
    intent = IntentParser().parse("Delete all files")

    with pytest.raises(PlanningError, match="not understood"):
        planner.plan(intent)


def test_plan_stop_has_no_actions(planner):
    """Stop intent should produce an empty plan."""
    intent = IntentParser().parse("cancel")
    plan = planner.plan(intent)

    assert intent.kind == IntentType.STOP
    assert plan.stop_requested is True
    assert plan.actions == ()