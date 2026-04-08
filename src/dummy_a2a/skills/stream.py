"""Stream skill -- responds with chunked streaming artifacts."""

import asyncio

from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    Artifact,
    Part,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)

NUM_CHUNKS = 5
CHUNK_DELAY = 0.1


class StreamSkill:
    async def handle(self, context: RequestContext, event_queue: EventQueue) -> None:
        user_input = context.get_user_input()
        text = user_input.strip()
        if text.lower().startswith("stream"):
            text = text[6:].strip() or "streaming response"

        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                status=TaskStatus(state=TaskState.TASK_STATE_WORKING),
            )
        )

        artifact_id = f"{context.task_id}-stream"
        for i in range(NUM_CHUNKS):
            is_last = i == NUM_CHUNKS - 1
            chunk_text = f"[{i + 1}/{NUM_CHUNKS}] {text}"

            await event_queue.enqueue_event(
                TaskArtifactUpdateEvent(
                    task_id=context.task_id,
                    context_id=context.context_id,
                    artifact=Artifact(
                        artifact_id=artifact_id,
                        name="stream",
                        parts=[Part(text=chunk_text)],
                    ),
                    append=i > 0,
                    last_chunk=is_last,
                )
            )
            if not is_last:
                await asyncio.sleep(CHUNK_DELAY)

        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                status=TaskStatus(state=TaskState.TASK_STATE_COMPLETED),
            )
        )
