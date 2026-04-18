"""Required extension test -- returns -32008 if required extension is missing."""

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
from a2a.utils.errors import ExtensionSupportRequiredError
from google.protobuf import struct_pb2

from dummy_a2a.agent_card import EXT_REQUIRED


class ExtRequiredSkill:
    async def handle(self, context: RequestContext, event_queue: EventQueue) -> None:
        if EXT_REQUIRED not in context.requested_extensions:
            raise ExtensionSupportRequiredError()

        data = struct_pb2.Value()
        data.struct_value.fields["extension"].string_value = EXT_REQUIRED
        data.struct_value.fields["status"].string_value = "satisfied"

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
                    artifact_id=f"{context.task_id}-ext-required",
                    name="required-extension-result",
                    parts=[Part(data=data, media_type="application/json")],
                    extensions=[EXT_REQUIRED],
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
