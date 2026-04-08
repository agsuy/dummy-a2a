"""Multi-artifact skill -- returns multiple artifacts with chunked delivery."""

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
from a2a.utils import new_text_artifact
from google.protobuf import struct_pb2

CHUNK_DELAY = 0.05


class MultiArtifactSkill:
    async def handle(self, context: RequestContext, event_queue: EventQueue) -> None:
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                status=TaskStatus(state=TaskState.TASK_STATE_WORKING),
            )
        )

        # Artifact 1: simple text (single chunk)
        await event_queue.enqueue_event(
            TaskArtifactUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                artifact=new_text_artifact(name="artifact-1", text="First artifact content."),
                last_chunk=True,
            )
        )

        # Artifact 2: chunked delivery (3 chunks)
        art2_id = f"{context.task_id}-art2"
        chunks = ["Beginning of ", "the second ", "artifact content."]
        for i, chunk in enumerate(chunks):
            await event_queue.enqueue_event(
                TaskArtifactUpdateEvent(
                    task_id=context.task_id,
                    context_id=context.context_id,
                    artifact=Artifact(
                        artifact_id=art2_id,
                        name="artifact-2",
                        parts=[Part(text=chunk)],
                    ),
                    append=i > 0,
                    last_chunk=i == len(chunks) - 1,
                )
            )
            await asyncio.sleep(CHUNK_DELAY)

        # Artifact 3: structured data
        data_value = struct_pb2.Value()
        data_value.struct_value.fields["artifact"].string_value = "third"
        data_value.struct_value.fields["number"].number_value = 3

        await event_queue.enqueue_event(
            TaskArtifactUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                artifact=Artifact(
                    artifact_id=f"{context.task_id}-art3",
                    name="artifact-3",
                    description="Structured data artifact",
                    parts=[Part(data=data_value, media_type="application/json")],
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
