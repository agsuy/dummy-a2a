"""Extension test skill -- exercises A2A extension negotiation."""

import datetime

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

from dummy_a2a.agent_card import (
    EXT_ECHO_METADATA,
    EXT_LOCALE,
    EXT_PRIORITY,
    EXT_REQUIRED,
    EXT_TIMESTAMP,
    EXT_TRACE_ID,
)

_BUILTIN_EXTENSIONS: frozenset[str] = frozenset(
    {
        EXT_ECHO_METADATA,
        EXT_TIMESTAMP,
        EXT_TRACE_ID,
        EXT_PRIORITY,
        EXT_LOCALE,
        EXT_REQUIRED,
    }
)


class ExtSkill:
    def __init__(self, extra_extensions: set[str] | None = None) -> None:
        self._known_extensions: frozenset[str] = (
            _BUILTIN_EXTENSIONS | extra_extensions if extra_extensions else _BUILTIN_EXTENSIONS
        )

    async def handle(self, context: RequestContext, event_queue: EventQueue) -> None:
        requested = context.requested_extensions
        activated: list[str] = []

        # Activate every requested extension we recognise
        for uri in requested:
            if uri in self._known_extensions:
                activated.append(uri)

        # Build response data
        data = struct_pb2.Value()
        s = data.struct_value

        req_list = s.fields["requested"].list_value
        for uri in sorted(requested):
            req_list.values.add().string_value = uri

        act_list = s.fields["activated"].list_value
        for uri in sorted(activated):
            act_list.values.add().string_value = uri

        if EXT_TIMESTAMP in activated:
            s.fields["timestamp"].string_value = datetime.datetime.now(
                datetime.timezone.utc
            ).isoformat()

        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                status=TaskStatus(state=TaskState.TASK_STATE_WORKING),
            )
        )

        artifact = Artifact(
            artifact_id=f"{context.task_id}-ext",
            name="extension-metadata",
            parts=[Part(data=data, media_type="application/json")],
            extensions=sorted(activated),
        )

        await event_queue.enqueue_event(
            TaskArtifactUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                artifact=artifact,
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
