"""Skill router and handler registry."""

from a2a.server.agent_execution import RequestContext
from a2a.types import Role, Task, TaskState

from dummy_a2a.skills.base import SkillHandler


class SkillRouter:
    """Routes user messages to the appropriate skill handler.

    Extracts the first word from the user's message as a command keyword
    and dispatches to the registered handler. Falls back to the first
    registered handler (or raises if none registered).
    """

    def __init__(self) -> None:
        self._handlers: dict[str, SkillHandler] = {}
        self._fallback: SkillHandler | None = None

    def register(self, command: str, handler: SkillHandler, *, fallback: bool = False) -> None:
        self._handlers[command.lower()] = handler
        if fallback or self._fallback is None:
            self._fallback = handler

    def resolve(self, context: RequestContext) -> SkillHandler:
        # For follow-up turns (interrupted tasks), resolve from the original command
        current_task = context.current_task
        if current_task is not None and current_task.status.state in (
            TaskState.TASK_STATE_INPUT_REQUIRED,
            TaskState.TASK_STATE_AUTH_REQUIRED,
        ):
            return self._resolve_from_history(current_task)

        user_input = context.get_user_input().strip()
        command = user_input.split()[0].lower() if user_input else ""
        handler = self._handlers.get(command) or self._fallback
        if handler is None:
            raise RuntimeError("No skills registered")
        return handler

    def _resolve_from_history(self, task: Task) -> SkillHandler:
        """Find the original command from the first user message in task history."""
        for msg in task.history:
            if msg.role == Role.ROLE_USER and msg.parts:
                first_part = msg.parts[0]
                if first_part.WhichOneof("content") == "text":
                    command = first_part.text.strip().split()[0].lower()
                    handler = self._handlers.get(command) or self._fallback
                    if handler is not None:
                        return handler
        if self._fallback is None:
            raise RuntimeError("No skills registered")
        return self._fallback


__all__ = ["SkillRouter", "SkillHandler"]
