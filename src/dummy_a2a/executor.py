"""Agent executor that routes messages to skill handlers."""

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import TaskState, TaskStatus, TaskStatusUpdateEvent

from dummy_a2a.skills import SkillRouter
from dummy_a2a.skills.base import SkillHandler


class DummyAgentExecutor(AgentExecutor):
    """Routes incoming messages to skill handlers based on the command keyword."""

    def __init__(self) -> None:
        self._router = SkillRouter()

    def register_all_skills(self) -> None:
        """Register all available skills."""
        from dummy_a2a.skills.auth_required import AuthRequiredSkill
        from dummy_a2a.skills.data_response import DataResponseSkill
        from dummy_a2a.skills.debug import DebugSkill
        from dummy_a2a.skills.echo import EchoSkill
        from dummy_a2a.skills.ext import ExtSkill
        from dummy_a2a.skills.ext_required import ExtRequiredSkill
        from dummy_a2a.skills.fail import FailSkill
        from dummy_a2a.skills.file_response import FileResponseSkill
        from dummy_a2a.skills.multi_artifact import MultiArtifactSkill
        from dummy_a2a.skills.multi_turn import MultiTurnSkill
        from dummy_a2a.skills.reject import RejectSkill
        from dummy_a2a.skills.slow_task import SlowTaskSkill
        from dummy_a2a.skills.stream import StreamSkill

        self._router.register("echo", EchoSkill(), fallback=True)
        self._router.register("stream", StreamSkill())
        self._router.register("ask", MultiTurnSkill())
        self._router.register("slow", SlowTaskSkill())
        self._router.register("fail", FailSkill())
        self._router.register("reject", RejectSkill())
        self._router.register("auth", AuthRequiredSkill())
        self._router.register("file", FileResponseSkill())
        self._router.register("data", DataResponseSkill())
        self._router.register("multi", MultiArtifactSkill())
        self._router.register("debug", DebugSkill())
        self._router.register("ext", ExtSkill())
        self._router.register("ext-required", ExtRequiredSkill())

    def register_plugin(self, command: str, handler: SkillHandler) -> None:
        """Register a plugin skill handler."""
        self._router.register(command, handler)

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        handler = self._router.resolve(context)
        await handler.handle(context, event_queue)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                status=TaskStatus(state=TaskState.TASK_STATE_CANCELED),
            )
        )
