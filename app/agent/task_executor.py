"""Execute validated task plans using approved desktop actions."""

import logging

from app.actions.desktop_controller import (
    DesktopActionError,
    DesktopController,
)
from app.agent.task_planner import TaskPlan

logger = logging.getLogger(__name__)


class TaskExecutionError(Exception):
    """Raised when a planned action cannot be executed."""


class TaskExecutor:
    """Execute the supported actions in a validated task plan."""

    def __init__(self, desktop: DesktopController | None = None) -> None:
        self.desktop = desktop or DesktopController()

    def execute(self, plan: TaskPlan) -> list[str]:
        """Execute a plan and return a result for each action."""

        if plan.stop_requested:
            return ["Stop requested. No actions executed."]

        results: list[str] = []

        for action in plan.actions:
            if action.action != "launch_app":
                raise TaskExecutionError(
                    f"Unsupported action: {action.action}"
                )

            try:
                app_name = self.desktop.launch_app(action.target)
                message = f"Launch request sent: {app_name}"
                logger.info(message)
                results.append(message)

            except (DesktopActionError, OSError) as exc:
                logger.exception(
                    "Application launch failed for %s",
                    action.target,
                )
                raise TaskExecutionError(
                    f"Could not launch '{action.target}': {exc}"
                ) from exc

        return results
