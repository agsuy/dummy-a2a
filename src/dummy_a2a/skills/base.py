"""Base skill handler protocol."""

from typing import Protocol

from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue


class SkillHandler(Protocol):
    """Protocol for A2A skill handlers.

    Each skill receives the request context and an event queue to publish
    task status updates and artifacts.
    """

    async def handle(self, context: RequestContext, event_queue: EventQueue) -> None: ...
