"""Build safe, structured plans from parsed intents."""

from dataclasses import dataclass

from app.actions.action_registry import ALLOWED_APPS
from app.agent.intent_parser import Intent, IntentType


class PlanningError(Exception):
    """Raised when an intent cannot be converted into a safe plan."""


@dataclass(frozen=True, slots=True)
class PlannedAction:
    """One validated action awaiting execution."""

    action: str
    target: str


@dataclass(frozen=True, slots=True)
class TaskPlan:
    """Immutable plan produced by the task planner."""

    actions: tuple[PlannedAction, ...]
    stop_requested: bool = False


class TaskPlanner:
    """Validate intents and create plans from allowlisted actions."""

    def plan(self, intent: Intent) -> TaskPlan:
        """Convert a supported intent into a validated task plan."""
        if intent.kind == IntentType.STOP:
            return TaskPlan(
                actions=(),
                stop_requested=True,
            )

        if intent.kind == IntentType.UNKNOWN:
            raise PlanningError(
                "Command not understood. Try 'Open Notepad' "
                "or another supported application."
            )

        if intent.kind == IntentType.LAUNCH_APP:
            target = (intent.target or "").strip().casefold()

            if target not in ALLOWED_APPS:
                allowed = ", ".join(sorted(ALLOWED_APPS))
                raise PlanningError(
                    f"Application '{target}' is not allowed. "
                    f"Supported applications: {allowed}."
                )

            return TaskPlan(
                actions=(
                    PlannedAction(
                        action="launch_app",
                        target=target,
                    ),
                )
            )

        # Fail closed if a future intent type is added without a plan.
        raise PlanningError(
            f"No planning rule exists for intent: {intent.kind}"
        )