"""Auth required skill -- transitions to AUTH_REQUIRED, then completes."""

from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from a2a.utils import new_agent_text_message, new_text_artifact


class AuthRequiredSkill:
    async def handle(self, context: RequestContext, event_queue: EventQueue) -> None:
        current_task = context.current_task
        is_follow_up = (
            current_task is not None
            and current_task.status.state == TaskState.TASK_STATE_AUTH_REQUIRED
        )

        if not is_follow_up:
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=context.task_id,
                    context_id=context.context_id,
                    status=TaskStatus(
                        state=TaskState.TASK_STATE_AUTH_REQUIRED,
                        message=new_agent_text_message(
                            text="Authentication required. Provide a token in your next message.",
                            context_id=context.context_id,
                            task_id=context.task_id,
                        ),
                    ),
                )
            )
        else:
            token = context.get_user_input().strip()
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
                    artifact=new_text_artifact(
                        name="auth-result",
                        text=f"Authenticated with token: {token}",
                    ),
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
