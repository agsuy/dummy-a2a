"""A2A spec compliance contracts.

Portable, runnable contract definitions that verify any A2A server
handles all protocol operations, task states, and content types correctly.

Usage as pytest parametrized tests::

    from dummy_a2a.contracts import a2a_contracts

    @pytest.mark.asyncio
    @pytest.mark.parametrize("contract", a2a_contracts, ids=lambda c: c.id)
    async def test_a2a_compliance(contract):
        await contract.verify("http://localhost:9000")

Usage as a standalone check (shared server, sequential)::

    from dummy_a2a.contracts import verify_a2a_compliance

    results = await verify_a2a_compliance("http://localhost:9000")
    for r in results:
        print(f"{'PASS' if r.passed else 'FAIL'} {r.contract_id}: {r.detail}")

Usage with isolated servers (concurrent)::

    from contextlib import asynccontextmanager
    from dummy_a2a import DummyA2AServer, verify_a2a_compliance

    @asynccontextmanager
    async def factory():
        async with DummyA2AServer(port=0) as server:
            yield server.url

    results = await verify_a2a_compliance(server_factory=factory)
"""

from __future__ import annotations

import asyncio
import json
import traceback
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# Core types
# ---------------------------------------------------------------------------


@dataclass
class ContractResult:
    contract_id: str
    passed: bool
    detail: str = ""
    traceback: str | None = None


@dataclass
class Contract:
    """A single verifiable A2A interaction contract."""

    id: str
    description: str
    category: str
    _verify_fn: Callable[[httpx.AsyncClient], Awaitable[None]] = field(repr=False)

    async def verify(self, base_url: str) -> ContractResult:
        """Run the contract against a server at *base_url*."""
        async with httpx.AsyncClient(base_url=base_url) as client:
            try:
                await self._verify_fn(client)
                return ContractResult(contract_id=self.id, passed=True)
            except AssertionError as e:
                return ContractResult(contract_id=self.id, passed=False, detail=str(e))
            except Exception as e:
                return ContractResult(
                    contract_id=self.id,
                    passed=False,
                    detail=f"{type(e).__name__}: {e}",
                    traceback=traceback.format_exc(),
                )

    def __repr__(self) -> str:
        return f"Contract({self.id!r})"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _rpc(method: str, params: dict[str, Any], req_id: int = 1) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}


def _msg_params(text: str, task_id: str | None = None) -> dict[str, Any]:
    msg: dict[str, Any] = {
        "messageId": str(uuid.uuid4()),
        "role": 1,
        "parts": [{"text": text}],
    }
    if task_id is not None:
        msg["taskId"] = task_id
    return {"message": msg}


async def _send(client: httpx.AsyncClient, text: str, task_id: str | None = None) -> dict:
    resp = await client.post("/", json=_rpc("SendMessage", _msg_params(text, task_id)))
    assert resp.status_code == 200, f"HTTP {resp.status_code}"
    body = resp.json()
    assert "result" in body, f"Expected result, got error: {body.get('error')}"
    return body["result"]["task"]


async def _rpc_call(client: httpx.AsyncClient, method: str, params: dict) -> dict:
    resp = await client.post("/", json=_rpc(method, params))
    assert resp.status_code == 200, f"HTTP {resp.status_code}"
    return resp.json()


async def _send_with_headers(
    client: httpx.AsyncClient,
    text: str,
    headers: dict[str, str],
    task_id: str | None = None,
) -> httpx.Response:
    """Send a message with custom headers, return raw response."""
    return await client.post(
        "/",
        json=_rpc("SendMessage", _msg_params(text, task_id)),
        headers=headers,
    )


# ---------------------------------------------------------------------------
# Contract definitions
# ---------------------------------------------------------------------------

_contracts: list[Contract] = []


def _contract(id: str, description: str, category: str):  # noqa: A002
    """Decorator to register a contract."""

    def decorator(fn):  # type: ignore[no-untyped-def]
        _contracts.append(
            Contract(id=id, description=description, category=category, _verify_fn=fn)
        )
        return fn

    return decorator


# --- Agent Card ---


@_contract("card.well-known", "Agent card served at well-known path", "agent-card")
async def _(client: httpx.AsyncClient) -> None:
    resp = await client.get("/.well-known/agent-card.json")
    assert resp.status_code == 200
    card = resp.json()
    assert card.get("name"), "Agent card must have a name"


@_contract("card.required-fields", "Agent card has all required fields", "agent-card")
async def _(client: httpx.AsyncClient) -> None:
    card = (await client.get("/.well-known/agent-card.json")).json()
    for field_name in [
        "name",
        "description",
        "version",
        "skills",
        "capabilities",
        "supportedInterfaces",
        "defaultInputModes",
        "defaultOutputModes",
    ]:
        assert field_name in card, f"Missing required field: {field_name}"


@_contract(
    "card.skills-have-required-fields",
    "Each skill has id, name, description, tags",
    "agent-card",
)
async def _(client: httpx.AsyncClient) -> None:
    card = (await client.get("/.well-known/agent-card.json")).json()
    for skill in card["skills"]:
        for f in ["id", "name", "description", "tags"]:
            assert f in skill, f"Skill {skill.get('id', '?')} missing field: {f}"


@_contract("card.interface-protocol-version", "Interface declares protocol version", "agent-card")
async def _(client: httpx.AsyncClient) -> None:
    card = (await client.get("/.well-known/agent-card.json")).json()
    interfaces = card.get("supportedInterfaces", [])
    assert len(interfaces) >= 1, "Must have at least one interface"
    assert interfaces[0].get("protocolVersion"), "Interface must declare protocolVersion"


@_contract(
    "card.extended-card",
    "Extended agent card available via GetExtendedAgentCard",
    "agent-card",
)
async def _(client: httpx.AsyncClient) -> None:
    card = (await client.get("/.well-known/agent-card.json")).json()
    caps = card.get("capabilities", {})
    if not caps.get("extendedAgentCard"):
        return  # Skip if not advertised
    resp = await _rpc_call(client, "GetExtendedAgentCard", {})
    assert "result" in resp, f"Expected extended card, got: {resp.get('error')}"
    assert "name" in resp["result"]
    assert "skills" in resp["result"]


# --- SendMessage (basic) ---


@_contract("send.completed", "SendMessage returns COMPLETED task", "send-message")
async def _(client: httpx.AsyncClient) -> None:
    task = await _send(client, "echo hello world")
    assert task["status"]["state"] == "TASK_STATE_COMPLETED"


@_contract("send.has-task-id", "SendMessage response includes task ID", "send-message")
async def _(client: httpx.AsyncClient) -> None:
    task = await _send(client, "echo test")
    assert task.get("id"), "Task must have an id"
    assert task.get("contextId"), "Task must have a contextId"


@_contract("send.has-artifacts", "Completed task includes artifacts", "send-message")
async def _(client: httpx.AsyncClient) -> None:
    task = await _send(client, "echo hello")
    assert len(task.get("artifacts", [])) >= 1, "Completed task should have artifacts"


@_contract("send.has-history", "Task includes message history", "send-message")
async def _(client: httpx.AsyncClient) -> None:
    task = await _send(client, "echo test")
    history = task.get("history", [])
    assert len(history) >= 1, "Task should include history"
    assert history[0]["role"] == "ROLE_USER"


# --- Task states ---


@_contract("state.failed", "SendMessage can return FAILED state", "task-state")
async def _(client: httpx.AsyncClient) -> None:
    task = await _send(client, "fail")
    assert task["status"]["state"] == "TASK_STATE_FAILED"
    assert task["status"].get("message"), "FAILED status should include a message"


@_contract("state.rejected", "SendMessage can return REJECTED state", "task-state")
async def _(client: httpx.AsyncClient) -> None:
    task = await _send(client, "reject")
    assert task["status"]["state"] == "TASK_STATE_REJECTED"


@_contract("state.input-required", "SendMessage can return INPUT_REQUIRED state", "task-state")
async def _(client: httpx.AsyncClient) -> None:
    task = await _send(client, "ask")
    assert task["status"]["state"] == "TASK_STATE_INPUT_REQUIRED"
    assert task["status"].get("message"), "INPUT_REQUIRED should include a prompt message"


@_contract("state.auth-required", "SendMessage can return AUTH_REQUIRED state", "task-state")
async def _(client: httpx.AsyncClient) -> None:
    task = await _send(client, "auth")
    assert task["status"]["state"] == "TASK_STATE_AUTH_REQUIRED"
    assert task["status"].get("message"), "AUTH_REQUIRED should include a message"


# --- Multi-turn ---


@_contract(
    "multi-turn.input-required-follow-up",
    "Follow-up message after INPUT_REQUIRED completes the task",
    "multi-turn",
)
async def _(client: httpx.AsyncClient) -> None:
    task = await _send(client, "ask")
    assert task["status"]["state"] == "TASK_STATE_INPUT_REQUIRED"
    task2 = await _send(client, "Claude", task_id=task["id"])
    assert task2["status"]["state"] == "TASK_STATE_COMPLETED"
    assert len(task2.get("artifacts", [])) >= 1


@_contract(
    "multi-turn.auth-required-follow-up",
    "Follow-up message after AUTH_REQUIRED completes the task",
    "multi-turn",
)
async def _(client: httpx.AsyncClient) -> None:
    task = await _send(client, "auth")
    assert task["status"]["state"] == "TASK_STATE_AUTH_REQUIRED"
    task2 = await _send(client, "my-token", task_id=task["id"])
    assert task2["status"]["state"] == "TASK_STATE_COMPLETED"


# --- GetTask ---


@_contract("get-task.retrieves-task", "GetTask returns a previously created task", "get-task")
async def _(client: httpx.AsyncClient) -> None:
    task = await _send(client, "echo hello")
    resp = await _rpc_call(client, "GetTask", {"id": task["id"]})
    assert "result" in resp
    assert resp["result"]["id"] == task["id"]
    assert resp["result"]["status"]["state"] == "TASK_STATE_COMPLETED"


@_contract("get-task.not-found", "GetTask returns error for nonexistent task", "get-task")
async def _(client: httpx.AsyncClient) -> None:
    resp = await _rpc_call(client, "GetTask", {"id": "nonexistent-" + str(uuid.uuid4())})
    assert "error" in resp


@_contract("get-task.includes-artifacts", "GetTask response includes artifacts", "get-task")
async def _(client: httpx.AsyncClient) -> None:
    task = await _send(client, "echo verify")
    resp = await _rpc_call(client, "GetTask", {"id": task["id"]})
    assert len(resp["result"].get("artifacts", [])) >= 1


# --- ListTasks ---


@_contract("list-tasks.returns-tasks", "ListTasks returns previously created tasks", "list-tasks")
async def _(client: httpx.AsyncClient) -> None:
    await _send(client, "echo one")
    await _send(client, "echo two")
    resp = await _rpc_call(client, "ListTasks", {})
    assert "result" in resp, f"Expected result, got: {resp.get('error')}"
    assert len(resp["result"]["tasks"]) >= 2


# --- CancelTask ---


@_contract("cancel.cancels-task", "CancelTask transitions task to CANCELED", "cancel-task")
async def _(client: httpx.AsyncClient) -> None:
    # Start a slow task via streaming to get task ID, then cancel
    task_id = None
    async with client.stream(
        "POST",
        "/",
        json=_rpc("SendStreamingMessage", _msg_params("slow")),
    ) as resp:
        async for line in resp.aiter_lines():
            if line.startswith("data: "):
                data = json.loads(line[6:])
                result = data.get("result", {})
                for key in ("statusUpdate", "artifactUpdate", "task"):
                    if key in result and "taskId" in result[key]:
                        task_id = result[key]["taskId"]
                        break
                if task_id:
                    break

    assert task_id is not None, "Should get task ID from streaming response"
    cancel_resp = await _rpc_call(client, "CancelTask", {"id": task_id})
    assert "result" in cancel_resp
    assert cancel_resp["result"]["status"]["state"] == "TASK_STATE_CANCELED"


@_contract(
    "cancel.nonexistent-task",
    "CancelTask returns error for nonexistent task",
    "cancel-task",
)
async def _(client: httpx.AsyncClient) -> None:
    resp = await _rpc_call(client, "CancelTask", {"id": "nonexistent-" + str(uuid.uuid4())})
    assert "error" in resp


# --- Streaming ---


@_contract("stream.sse-events", "SendStreamingMessage yields SSE events", "streaming")
async def _(client: httpx.AsyncClient) -> None:
    events = []
    async with client.stream(
        "POST",
        "/",
        json=_rpc("SendStreamingMessage", _msg_params("stream hello")),
    ) as resp:
        assert resp.status_code == 200
        async for line in resp.aiter_lines():
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))

    assert len(events) >= 2, "Should yield multiple events"
    status_events = [e for e in events if "statusUpdate" in e.get("result", {})]
    artifact_events = [e for e in events if "artifactUpdate" in e.get("result", {})]
    assert len(status_events) >= 2, "Should have at least working + completed status"
    assert len(artifact_events) >= 1, "Should have artifact events"

    last_status = status_events[-1]["result"]["statusUpdate"]["status"]
    assert last_status["state"] == "TASK_STATE_COMPLETED"


# --- Content types ---


@_contract("content.text-part", "TextPart artifact returned correctly", "content-types")
async def _(client: httpx.AsyncClient) -> None:
    task = await _send(client, "echo hello")
    part = task["artifacts"][0]["parts"][0]
    assert "text" in part, "Should have text field"


@_contract("content.file-part", "FilePart artifact with raw bytes", "content-types")
async def _(client: httpx.AsyncClient) -> None:
    task = await _send(client, "file")
    part = task["artifacts"][0]["parts"][0]
    assert "raw" in part, "Should have raw bytes"
    assert part.get("filename"), "Should have filename"
    assert part.get("mediaType"), "Should have mediaType"


@_contract("content.data-part", "DataPart artifact with structured JSON", "content-types")
async def _(client: httpx.AsyncClient) -> None:
    task = await _send(client, "data")
    part = task["artifacts"][0]["parts"][0]
    assert "data" in part, "Should have data field"
    assert isinstance(part["data"], dict), "Data should be a dict"
    assert part.get("mediaType") == "application/json"


@_contract(
    "content.multi-artifact",
    "Multiple artifacts with different types in one task",
    "content-types",
)
async def _(client: httpx.AsyncClient) -> None:
    task = await _send(client, "multi")
    artifacts = task.get("artifacts", [])
    assert len(artifacts) >= 3, "Should return at least 3 artifacts"


# --- Push notification config ---


@_contract(
    "push.create-config",
    "CreateTaskPushNotificationConfig stores a config",
    "push-notifications",
)
async def _(client: httpx.AsyncClient) -> None:
    task = await _send(client, "echo test")
    resp = await _rpc_call(
        client,
        "CreateTaskPushNotificationConfig",
        {"taskId": task["id"], "url": "http://example.com/webhook"},
    )
    assert "result" in resp, f"Expected result, got: {resp.get('error')}"


@_contract(
    "push.delete-config",
    "DeleteTaskPushNotificationConfig removes a config",
    "push-notifications",
)
async def _(client: httpx.AsyncClient) -> None:
    task = await _send(client, "echo test")
    create_resp = await _rpc_call(
        client,
        "CreateTaskPushNotificationConfig",
        {"taskId": task["id"], "url": "http://example.com/webhook"},
    )
    config_id = create_resp["result"].get("id")
    if config_id:
        del_resp = await _rpc_call(
            client,
            "DeleteTaskPushNotificationConfig",
            {"taskId": task["id"], "id": config_id},
        )
        assert "error" not in del_resp


# --- Error handling ---


@_contract("error.method-not-found", "Unknown method returns -32601", "errors")
async def _(client: httpx.AsyncClient) -> None:
    resp = await _rpc_call(client, "NonExistentMethod", {})
    assert "error" in resp
    assert resp["error"]["code"] == -32601


@_contract("error.invalid-jsonrpc", "Invalid jsonrpc version returns error", "errors")
async def _(client: httpx.AsyncClient) -> None:
    resp = await client.post(
        "/", json={"jsonrpc": "1.0", "id": 1, "method": "GetTask", "params": {"id": "x"}}
    )
    assert "error" in resp.json()


# --- Extensions ---

_EXT_HEADER = "X-A2A-Extensions"


@_contract(
    "ext.card-advertises-extensions",
    "Agent card capabilities.extensions lists extensions with uri and description",
    "extensions",
)
async def _(client: httpx.AsyncClient) -> None:
    card = (await client.get("/.well-known/agent-card.json")).json()
    exts = card.get("capabilities", {}).get("extensions", [])
    assert len(exts) >= 1, "Card should advertise at least one extension"
    for ext in exts:
        assert ext.get("uri"), "Extension must have a uri"
        assert ext.get("description"), "Extension must have a description"


@_contract(
    "ext.negotiation-activates",
    "Requesting a known extension activates it (response header)",
    "extensions",
)
async def _(client: httpx.AsyncClient) -> None:
    # Discover an extension URI from the card
    card = (await client.get("/.well-known/agent-card.json")).json()
    exts = card.get("capabilities", {}).get("extensions", [])
    non_required = [e for e in exts if not e.get("required")]
    assert non_required, "Need at least one non-required extension"
    uri = non_required[0]["uri"]

    resp = await _send_with_headers(client, "ext", {_EXT_HEADER: uri})
    assert resp.status_code == 200
    activated = resp.headers.get(_EXT_HEADER, "")
    assert uri in activated, f"Expected {uri} in response header, got: {activated}"


@_contract(
    "ext.unknown-ignored",
    "Unknown extension URI is ignored without error",
    "extensions",
)
async def _(client: httpx.AsyncClient) -> None:
    resp = await _send_with_headers(client, "ext", {_EXT_HEADER: "urn:a2a:unknown:nonexistent"})
    assert resp.status_code == 200
    body = resp.json()
    assert "result" in body, f"Expected result, got: {body.get('error')}"


@_contract(
    "ext.artifact-tagged",
    "Activated extensions appear in artifact.extensions",
    "extensions",
)
async def _(client: httpx.AsyncClient) -> None:
    card = (await client.get("/.well-known/agent-card.json")).json()
    exts = card.get("capabilities", {}).get("extensions", [])
    non_required = [e for e in exts if not e.get("required")]
    assert non_required, "Need at least one non-required extension"
    uri = non_required[0]["uri"]

    resp = await _send_with_headers(client, "ext", {_EXT_HEADER: uri})
    task = resp.json()["result"]["task"]
    artifact = task["artifacts"][0]
    assert uri in artifact.get("extensions", []), (
        "Artifact should be tagged with activated extension"
    )


@_contract(
    "ext.multiple-extensions",
    "Multiple requested extensions can be activated simultaneously",
    "extensions",
)
async def _(client: httpx.AsyncClient) -> None:
    card = (await client.get("/.well-known/agent-card.json")).json()
    exts = card.get("capabilities", {}).get("extensions", [])
    non_required = [e for e in exts if not e.get("required")]
    if len(non_required) < 2:
        return  # Skip if fewer than 2 non-required extensions
    uris = [e["uri"] for e in non_required[:2]]

    resp = await _send_with_headers(client, "ext", {_EXT_HEADER: ", ".join(uris)})
    activated = resp.headers.get(_EXT_HEADER, "")
    for uri in uris:
        assert uri in activated, f"Expected {uri} in activated extensions"


@_contract(
    "ext.params-in-card",
    "Extension with params has them accessible in the agent card",
    "extensions",
)
async def _(client: httpx.AsyncClient) -> None:
    card = (await client.get("/.well-known/agent-card.json")).json()
    exts = card.get("capabilities", {}).get("extensions", [])
    with_params = [e for e in exts if e.get("params")]
    if not with_params:
        return  # Skip if no extensions have params
    ext = with_params[0]
    assert isinstance(ext["params"], dict), "Params should be a dict"


@_contract(
    "ext.required-enforced",
    "Missing required extension returns -32008",
    "extensions",
)
async def _(client: httpx.AsyncClient) -> None:
    card = (await client.get("/.well-known/agent-card.json")).json()
    exts = card.get("capabilities", {}).get("extensions", [])
    required = [e for e in exts if e.get("required")]
    if not required:
        return  # Skip if no required extensions
    # Send ext-required command without the required extension header
    resp = await client.post("/", json=_rpc("SendMessage", _msg_params("ext-required")))
    body = resp.json()
    assert "error" in body, "Expected error when required extension is missing"
    assert body["error"]["code"] == -32008, f"Expected -32008, got {body['error']['code']}"


@_contract(
    "ext.required-satisfied",
    "Providing required extension allows request to succeed",
    "extensions",
)
async def _(client: httpx.AsyncClient) -> None:
    card = (await client.get("/.well-known/agent-card.json")).json()
    exts = card.get("capabilities", {}).get("extensions", [])
    required = [e for e in exts if e.get("required")]
    if not required:
        return  # Skip if no required extensions
    uri = required[0]["uri"]
    resp = await _send_with_headers(client, "ext-required", {_EXT_HEADER: uri})
    body = resp.json()
    assert "result" in body, f"Expected result, got: {body.get('error')}"
    assert body["result"]["task"]["status"]["state"] == "TASK_STATE_COMPLETED"
    assert uri in resp.headers.get(_EXT_HEADER, "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

a2a_contracts: list[Contract] = list(_contracts)
"""All registered A2A compliance contracts."""


ServerFactory = Callable[[], AsyncIterator[str]]
"""Async context manager factory that yields a base URL for a fresh server."""


async def verify_a2a_compliance(
    base_url: str | None = None,
    *,
    server_factory: ServerFactory | None = None,
    categories: list[str] | None = None,
) -> list[ContractResult]:
    """Run all contracts against a server and return results.

    Provide either *base_url* (shared server, sequential execution) or
    *server_factory* (fresh server per contract, concurrent execution).

    Args:
        base_url: The A2A server URL (e.g. "http://localhost:9000").
            Contracts run sequentially and share server state.
        server_factory: An async context manager factory that yields a base URL
            for an isolated server instance. Each contract gets its own server
            and contracts run concurrently. Example::

                from dummy_a2a import DummyA2AServer

                @asynccontextmanager
                async def factory():
                    async with DummyA2AServer(port=0) as server:
                        yield server.url

                results = await verify_a2a_compliance(server_factory=factory)

        categories: Optional list of categories to filter
            (e.g. ["agent-card", "send-message"]). If None, runs all contracts.

    Returns:
        List of ContractResult with pass/fail status for each contract.
    """
    if base_url is None and server_factory is None:
        raise ValueError("Provide either base_url or server_factory")

    contracts = a2a_contracts
    if categories:
        contracts = [c for c in contracts if c.category in categories]

    if server_factory is not None:

        async def _run_isolated(contract: Contract) -> ContractResult:
            ctx = asynccontextmanager(server_factory)()
            async with ctx as url:
                return await contract.verify(url)

        return list(await asyncio.gather(*[_run_isolated(c) for c in contracts]))

    assert base_url is not None
    results = []
    for contract in contracts:
        result = await contract.verify(base_url)
        results.append(result)
    return results
