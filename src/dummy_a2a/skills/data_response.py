"""Data response skill -- returns a DataPart (structured JSON) artifact."""

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
from google.protobuf import struct_pb2


def _build_sample_data() -> struct_pb2.Value:
    """Build a sample structured data Value."""
    value = struct_pb2.Value()
    struct = value.struct_value
    struct.fields["agent"].string_value = "dummy-a2a"
    struct.fields["version"].string_value = "1.0.0"
    struct.fields["status"].string_value = "ok"
    struct.fields["count"].number_value = 42

    items = struct.fields["items"].list_value
    for item in ["alpha", "beta", "gamma"]:
        items.values.add().string_value = item

    return value


class DataResponseSkill:
    async def handle(self, context: RequestContext, event_queue: EventQueue) -> None:
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
                artifact=Artifact(
                    artifact_id=f"{context.task_id}-data",
                    name="sample-data",
                    description="Sample structured JSON data",
                    parts=[Part(data=_build_sample_data(), media_type="application/json")],
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
