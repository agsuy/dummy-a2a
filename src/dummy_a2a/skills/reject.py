"""Reject skill -- immediately rejects the task."""

from a2a.helpers import new_text_message
from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue
from a2a.types import TaskState, TaskStatus, TaskStatusUpdateEvent


class RejectSkill:
    async def handle(self, context: RequestContext, event_queue: EventQueue) -> None:
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                status=TaskStatus(
                    state=TaskState.TASK_STATE_REJECTED,
                    message=new_text_message(
                        text="Task rejected for testing purposes.",
                        context_id=context.context_id,
                        task_id=context.task_id,
                    ),
                ),
            )
        )
