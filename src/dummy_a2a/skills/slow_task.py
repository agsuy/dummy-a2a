"""Slow task skill -- runs for ~10 seconds with progress updates."""

import asyncio

from a2a.helpers import new_text_artifact, new_text_message
from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)

STEPS = 10
STEP_DELAY = 1.0


class SlowTaskSkill:
    async def handle(self, context: RequestContext, event_queue: EventQueue) -> None:
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                status=TaskStatus(
                    state=TaskState.TASK_STATE_WORKING,
                    message=new_text_message(
                        text="Starting slow task...",
                        context_id=context.context_id,
                        task_id=context.task_id,
                    ),
                ),
            )
        )

        for i in range(STEPS):
            await asyncio.sleep(STEP_DELAY)
            is_closed = getattr(event_queue, "is_closed", None)
            if callable(is_closed) and is_closed():
                return
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=context.task_id,
                    context_id=context.context_id,
                    status=TaskStatus(
                        state=TaskState.TASK_STATE_WORKING,
                        message=new_text_message(
                            text=f"Progress: {i + 1}/{STEPS}",
                            context_id=context.context_id,
                            task_id=context.task_id,
                        ),
                    ),
                )
            )

        await event_queue.enqueue_event(
            TaskArtifactUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                artifact=new_text_artifact(name="result", text="Slow task completed."),
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
