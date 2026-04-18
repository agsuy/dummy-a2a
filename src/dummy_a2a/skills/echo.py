"""Echo skill -- returns the user's input as an artifact."""

from a2a.helpers import new_text_artifact
from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)


class EchoSkill:
    """Echoes back the user's input text (minus the 'echo' command prefix)."""

    async def handle(self, context: RequestContext, event_queue: EventQueue) -> None:
        user_input = context.get_user_input()
        text = _strip_command(user_input, "echo")

        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                status=TaskStatus(state=TaskState.TASK_STATE_WORKING),
            )
        )

        await event_queue.enqueue_event(
            TaskArtifactUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                artifact=new_text_artifact(name="echo", text=text),
                last_chunk=True,
            )
        )

        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                status=TaskStatus(state=TaskState.TASK_STATE_COMPLETED),
            )
        )


def _strip_command(text: str, command: str) -> str:
    """Remove the command prefix from user input, if present."""
    stripped = text.strip()
    if stripped.lower().startswith(command):
        stripped = stripped[len(command) :].strip()
    return stripped or text.strip()
