"""Tests for the generic extension plugin system."""

import logging

import pytest
from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue
from a2a.types import AgentExtension, AgentSkill, TaskState, TaskStatus, TaskStatusUpdateEvent
from a2a.utils import new_text_artifact

from dummy_a2a import A2APlugin, DummyA2AServer
from dummy_a2a._utils import A2A_JSONRPC_DEFAULT_HEADERS
from dummy_a2a.agent_card import EXT_ECHO_METADATA
from dummy_a2a.skills import SkillRouter
from tests.helpers import rpc_request, send, send_message_params

pytestmark = pytest.mark.asyncio

PLUGIN_URI = "urn:a2a:test:plugin-ext"
EXTENSION_HEADER = "X-A2A-Extensions"


class StubSkill:
    """Minimal skill that completes with a text artifact."""

    async def handle(self, context: RequestContext, event_queue: EventQueue) -> None:
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                status=TaskStatus(state=TaskState.TASK_STATE_WORKING),
            )
        )
        from a2a.types import TaskArtifactUpdateEvent

        await event_queue.enqueue_event(
            TaskArtifactUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                artifact=new_text_artifact(name="plugin-out", text="plugin response"),
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


def _make_plugin(
    uri: str = PLUGIN_URI,
    command: str = "plugtest",
) -> A2APlugin:
    return A2APlugin(
        extension=AgentExtension(uri=uri, description="Test plugin extension"),
        skill=AgentSkill(
            id=command,
            name="Plugin Test",
            description="A test plugin skill.",
            tags=["test", "plugin"],
            examples=[command],
            input_modes=["text/plain"],
            output_modes=["text/plain"],
        ),
        command=command,
        handler=StubSkill(),
    )


# ---------------------------------------------------------------------------
# Agent card advertising
# ---------------------------------------------------------------------------


async def test_plugin_extension_in_agent_card():
    """Plugin extension appears in the agent card capabilities."""
    plugin = _make_plugin()
    async with DummyA2AServer(port=0, extensions=[plugin]) as server:
        import httpx

        async with httpx.AsyncClient(
            base_url=server.url,
            headers=A2A_JSONRPC_DEFAULT_HEADERS,
        ) as client:
            resp = await client.get("/.well-known/agent-card.json")
            card = resp.json()
            uris = [e["uri"] for e in card["capabilities"]["extensions"]]
            assert PLUGIN_URI in uris


async def test_plugin_skill_in_agent_card():
    """Plugin skill appears in the agent card skills list."""
    plugin = _make_plugin()
    async with DummyA2AServer(port=0, extensions=[plugin]) as server:
        import httpx

        async with httpx.AsyncClient(
            base_url=server.url,
            headers=A2A_JSONRPC_DEFAULT_HEADERS,
        ) as client:
            resp = await client.get("/.well-known/agent-card.json")
            card = resp.json()
            skill_ids = [s["id"] for s in card["skills"]]
            assert "plugtest" in skill_ids


# ---------------------------------------------------------------------------
# Command routing
# ---------------------------------------------------------------------------


async def test_plugin_command_routes_to_handler():
    """Plugin command keyword routes to the plugin handler."""
    plugin = _make_plugin()
    async with DummyA2AServer(port=0, extensions=[plugin]) as server:
        import httpx

        async with httpx.AsyncClient(
            base_url=server.url,
            headers=A2A_JSONRPC_DEFAULT_HEADERS,
        ) as client:
            task = await send(client, "plugtest hello")
            assert task["status"]["state"] == "TASK_STATE_COMPLETED"
            assert task["artifacts"][0]["parts"][0]["text"] == "plugin response"


# ---------------------------------------------------------------------------
# Extension negotiation via ext skill
# ---------------------------------------------------------------------------


async def test_ext_activates_plugin_extension():
    """The ext skill activates plugin extensions via header negotiation."""
    plugin = _make_plugin()
    async with DummyA2AServer(port=0, extensions=[plugin]) as server:
        import httpx

        async with httpx.AsyncClient(
            base_url=server.url,
            headers=A2A_JSONRPC_DEFAULT_HEADERS,
        ) as client:
            resp = await client.post(
                "/",
                json=rpc_request("SendMessage", send_message_params("ext")),
                headers={EXTENSION_HEADER: PLUGIN_URI},
            )
            assert resp.status_code == 200
            activated = resp.headers.get(EXTENSION_HEADER, "")
            assert PLUGIN_URI in activated


async def test_ext_artifact_tagged_with_plugin_extension():
    """Ext skill tags artifact with plugin extension URI."""
    plugin = _make_plugin()
    async with DummyA2AServer(port=0, extensions=[plugin]) as server:
        import httpx

        async with httpx.AsyncClient(
            base_url=server.url,
            headers=A2A_JSONRPC_DEFAULT_HEADERS,
        ) as client:
            resp = await client.post(
                "/",
                json=rpc_request("SendMessage", send_message_params("ext")),
                headers={EXTENSION_HEADER: PLUGIN_URI},
            )
            task = resp.json()["result"]["task"]
            artifact = task["artifacts"][0]
            assert PLUGIN_URI in artifact.get("extensions", [])


# ---------------------------------------------------------------------------
# Collision handling
# ---------------------------------------------------------------------------


async def test_duplicate_extension_uri_raises():
    """Duplicate extension URI raises ValueError at startup."""
    plugin1 = _make_plugin(uri=PLUGIN_URI, command="plug1")
    plugin2 = _make_plugin(uri=PLUGIN_URI, command="plug2")
    with pytest.raises(ValueError, match="Duplicate extension URI"):
        async with DummyA2AServer(port=0, extensions=[plugin1, plugin2]):
            pass


async def test_builtin_extension_uri_raises():
    """Plugin with a built-in extension URI raises ValueError."""
    plugin = _make_plugin(uri=EXT_ECHO_METADATA, command="clash")
    with pytest.raises(ValueError, match="Duplicate extension URI"):
        async with DummyA2AServer(port=0, extensions=[plugin]):
            pass


async def test_command_collision_logs_warning(caplog):
    """Overriding an existing command logs a warning."""
    router = SkillRouter()
    stub = StubSkill()
    router.register("echo", stub)
    with caplog.at_level(logging.WARNING):
        router.register("echo", stub)
    assert "overridden" in caplog.text


# ---------------------------------------------------------------------------
# Backward compatibility
# ---------------------------------------------------------------------------


async def test_no_plugins_works():
    """Server with no plugins works identically to before."""
    async with DummyA2AServer(port=0) as server:
        import httpx

        async with httpx.AsyncClient(
            base_url=server.url,
            headers=A2A_JSONRPC_DEFAULT_HEADERS,
        ) as client:
            task = await send(client, "echo hello")
            assert task["status"]["state"] == "TASK_STATE_COMPLETED"
