"""Debug skill -- returns internal server state (extended card only)."""

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


class DebugSkill:
    async def handle(self, context: RequestContext, event_queue: EventQueue) -> None:
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                status=TaskStatus(state=TaskState.TASK_STATE_WORKING),
            )
        )

        data = struct_pb2.Value()
        s = data.struct_value
        s.fields["task_id"].string_value = context.task_id or ""
        s.fields["context_id"].string_value = context.context_id or ""
        s.fields["user_input"].string_value = context.get_user_input() or ""
        s.fields["has_current_task"].bool_value = context.current_task is not None

        await event_queue.enqueue_event(
            TaskArtifactUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                artifact=Artifact(
                    artifact_id=f"{context.task_id}-debug",
                    name="debug-info",
                    description="Internal server state",
                    parts=[Part(data=data, media_type="application/json")],
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
