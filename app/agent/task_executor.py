
"""Execute validated task plans using approved desktop actions."""

import logging
import time

from app.actions.desktop_controller import (
    DesktopActionError,
    DesktopController,
)
from app.actions.whatsapp_contact_search import (
    WhatsAppContactSearch,
    WhatsAppSearchError,
)
from app.agent.task_planner import TaskPlan
from app.vision.screen_observer import (
    ScreenObservationError,
    ScreenObserver,
)

logger = logging.getLogger(__name__)


class TaskExecutionError(Exception):
    """Raised when a planned action cannot be executed."""


class TaskExecutor:
    """Execute the supported actions in a validated task plan."""

    def __init__(
        self,
        desktop: DesktopController | None = None,
        observer: ScreenObserver | None = None,
        contact_search: WhatsAppContactSearch | None = None,
    ) -> None:
        self.desktop = desktop or DesktopController()
        self.observer = observer or ScreenObserver()
        self.contact_search = contact_search or WhatsAppContactSearch()

    def execute(self, plan: TaskPlan) -> list[str]:
        """Execute a validated plan and return action results."""
        if plan.stop_requested:
            return ["Stop requested. No actions executed."]

        results: list[str] = []

        for action in plan.actions:
            try:
                if action.action == "launch_app":
                    app_name = self.desktop.launch_app(action.target)
                    message = f"Launch request sent: {app_name}"

                    logger.info(message)
                    results.append(message)
                    continue

                if action.action == "open_whatsapp_chat":
                    # Launch through the existing allowlisted controller.
                    self.desktop.launch_app("whatsapp")

                    # Wait for the WhatsApp window to become visible.
                    deadline = time.monotonic() + 15
                    window_found = False

                    while time.monotonic() < deadline:
                        windows = self.observer.list_visible_windows()

                        if any(
                            window.title.strip().casefold() == "whatsapp"
                            for window in windows
                        ):
                            window_found = True
                            break

                        time.sleep(0.25)

                    if not window_found:
                        raise TaskExecutionError(
                            "WhatsApp did not become visible within "
                            "15 seconds."
                        )

                    # Search for the contact and open only a unique match.
                    result = self.contact_search.search_and_open(
                        action.target
                    )

                    if not result.opened_chat.verified:
                        raise TaskExecutionError(
                            "The requested WhatsApp chat could not "
                            "be verified."
                        )

                    message = (
                        "Opened and verified WhatsApp chat: "
                        f"{result.requested_contact}"
                    )

                    logger.info(message)
                    results.append(message)
                    continue

                raise TaskExecutionError(
                    f"Unsupported action: {action.action}"
                )

            except TaskExecutionError:
                raise

            except (
                DesktopActionError,
                WhatsAppSearchError,
                ScreenObservationError,
                OSError,
            ) as exc:
                logger.exception(
                    "Execution failed for action %s targeting %s",
                    action.action,
                    action.target,
                )

                raise TaskExecutionError(
                    f"Could not execute '{action.action}' "
                    f"for '{action.target}': {exc}"
                ) from exc

        return results
