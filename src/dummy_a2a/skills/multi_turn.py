"""Multi-turn skill -- asks for input, then completes."""

from a2a.helpers import new_text_artifact, new_text_message
from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)


class MultiTurnSkill:
    async def handle(self, context: RequestContext, event_queue: EventQueue) -> None:
        current_task = context.current_task
        is_follow_up = (
            current_task is not None
            and current_task.status.state == TaskState.TASK_STATE_INPUT_REQUIRED
        )

        if not is_follow_up:
            # First turn: ask for input
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=context.task_id,
                    context_id=context.context_id,
                    status=TaskStatus(
                        state=TaskState.TASK_STATE_INPUT_REQUIRED,
                        message=new_text_message(
                            text="What is your name?",
                            context_id=context.context_id,
                            task_id=context.task_id,
                        ),
                    ),
                )
            )
        else:
            # Follow-up turn: complete with greeting
            name = context.get_user_input().strip()
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
                    artifact=new_text_artifact(name="greeting", text=f"Hello, {name}!"),
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
