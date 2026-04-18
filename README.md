# dummy-a2a

[![CI](https://github.com/agsuy/dummy-a2a/actions/workflows/ci.yml/badge.svg)](https://github.com/agsuy/dummy-a2a/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/dummy-a2a.svg?logo=pypi&logoColor=white&label=version)](https://pypi.org/project/dummy-a2a/)
[![Python](https://img.shields.io/pypi/pyversions/dummy-a2a.svg?logo=python&logoColor=ffd43b&label=python)](https://pypi.org/project/dummy-a2a/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://github.com/agsuy/dummy-a2a/blob/main/LICENSE)

[![a2a-sdk latest on PyPI](https://img.shields.io/pypi/v/a2a-sdk.svg?logo=pypi&logoColor=white&label=a2a-sdk%20latest)](https://pypi.org/project/a2a-sdk/)
[![a2a-sdk pinned by dummy-a2a](https://img.shields.io/badge/a2a--sdk%20pin-1.0.0a3-informational)](https://github.com/agsuy/dummy-a2a/blob/main/pyproject.toml)

A programmable A2A 1.0 test agent. Send it a command keyword, get spec-compliant behavior back.

Use it to **test your A2A client**, **validate spec compliance**, **test extension plugins**, or **run portable contracts** against any server.

The badges above compare **latest `a2a-sdk` on PyPI** with **the exact version pinned in `pyproject.toml`**; CI fails if PyPI is ahead so we remember to bump the pin. Covers **11/11 operations**, **all 8 task states**, **3 content types**, and **full extension negotiation**.

Codebase is intentionally small (~2300 LOC) and modular. Each skill is a self-contained file under 80 lines, each contract is an independent HTTP assertion. When and if spec changes, the blast radius is typically one skill or one contract and easy to update.

### What you can validate

| Goal | How |
|------|-----|
| **Validate your client** | Point your client at the dummy server. Send commands (`echo`, `fail`, `stream`, `ask`, `ext`, ...) and assert your client handles each response shape, state transition, SSE stream, and error code correctly. |
| **Validate your server** | Run the 46 portable contracts against your server. Contracts are dogfooded against the dummy server in CI, so you know they're correct. |
| **Validate your extensions** | Register your extension as a plugin via `A2APlugin` and test it end-to-end: agent card advertising, header negotiation, artifact tagging, and multi-extension activation. |

---

## Table of Contents

- [Install](#install)
- [Quick Start](#quick-start) -- get running in 30 seconds
  - [Standalone server](#1-standalone-server) (HTTP, HTTPS, Docker)
  - [As a library](#2-as-a-library)
  - [Pytest fixtures](#3-pytest-fixtures) (HTTP + HTTPS)
- [Commands](#commands) -- 14 command keywords
- [Extensions](#extensions) -- A2A 1.0 extension negotiation
  - [How it works](#how-it-works)
  - [Registered extensions](#registered-extensions)
  - [Extension plugins](#extension-plugins) -- test your own extension
  - [Testing with curl](#testing-extensions-with-curl)
  - [Testing with pytest](#testing-extensions-with-pytest)
  - [Testing with contracts](#testing-extensions-with-portable-contracts)
- [Contract Testing](#contract-testing) -- 46 portable compliance contracts
  - [Run against your server](#run-contracts-against-your-server)
  - [Run as pytest](#run-contracts-as-pytest)
  - [Contract list](#contract-list)
- [Spec Coverage](#spec-coverage)
- [Development](#development)
- [License](#license)

---

## Install

```bash
pip install dummy-a2a
```

Or from source:

```bash
git clone https://github.com/agsuy/dummy-a2a && cd dummy-a2a
uv sync --dev
```

---

## Quick Start

### 1. Standalone server

```bash
# HTTP
dummy-a2a --port 9000

# HTTPS
dummy-a2a --port 9443 --ssl-certfile cert.pem --ssl-keyfile key.pem

# Docker
docker run -p 9000:9000 ghcr.io/agsuy/dummy-a2a

# Quiet mode (suppress a2a SDK noise like push-notification errors)
dummy-a2a --sdk-log-level CRITICAL

# Verbose mode (see all server and SDK activity)
dummy-a2a --log-level info --sdk-log-level DEBUG
```

`--log-level` controls the server (uvicorn) logger, `--sdk-log-level` controls the `a2a` SDK logger independently. Both accept standard Python log levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).

As a library:

```python
# Silence SDK noise programmatically
async with DummyA2AServer(port=0, sdk_log_level="CRITICAL") as server:
    ...

# Verbose server + quiet SDK
async with DummyA2AServer(port=0, log_level="info", sdk_log_level="ERROR") as server:
    ...
```

Try it out:

```bash
# Agent card
curl http://localhost:9000/.well-known/agent-card.json
# → {"name": "Dummy A2A Test Agent", "skills": [...], "capabilities": {...}, ...}

# Send a message
curl -X POST http://localhost:9000/ -H 'Content-Type: application/json' -d '{
  "jsonrpc": "2.0", "id": 1,
  "method": "SendMessage",
  "params": {"message": {"messageId": "1", "role": 1, "parts": [{"text": "echo hello"}]}}
}'
# → {"result": {"task": {"id": "...", "contextId": "...", "status": {"state": "TASK_STATE_COMPLETED"}, "artifacts": [{"parts": [{"text": "hello"}]}], "history": [...]}}, "id": 1, "jsonrpc": "2.0"}

# Trigger a failure
curl -X POST http://localhost:9000/ -H 'Content-Type: application/json' -d '{
  "jsonrpc": "2.0", "id": 1,
  "method": "SendMessage",
  "params": {"message": {"messageId": "1", "role": 1, "parts": [{"text": "fail"}]}}
}'
# → {"result": {"task": {"id": "...", "status": {"state": "TASK_STATE_FAILED", "message": {"role": "ROLE_AGENT", "parts": [{"text": "Deliberate failure for testing purposes."}]}}, "history": [...]}}, "id": 1, "jsonrpc": "2.0"}
```

### 2. As a library

```python
from dummy_a2a import DummyA2AServer

async with DummyA2AServer(port=0) as server:
    print(server.url)  # http://127.0.0.1:<random>
    # query with any HTTP client, any language, any A2A SDK

# With HTTPS
async with DummyA2AServer(port=0, ssl_certfile="cert.pem", ssl_keyfile="key.pem") as server:
    print(server.url)  # https://127.0.0.1:<random>
```

### 3. Pytest fixtures

Drop this in your `conftest.py`:

```python
from dummy_a2a.testing import a2a_server, a2a_url, a2a_http  # noqa: F401
```

Write tests:

```python
import pytest

@pytest.mark.asyncio
async def test_echo(a2a_url):
    result = await my_a2a_client.send(a2a_url, "echo hello")
    assert result.state == "TASK_STATE_COMPLETED"

@pytest.mark.asyncio
async def test_failure(a2a_url):
    result = await my_a2a_client.send(a2a_url, "fail")
    assert result.state == "TASK_STATE_FAILED"
```

For HTTPS testing:

```python
from dummy_a2a.testing import a2a_https_server, a2a_https_url, a2a_https_http  # noqa: F401

@pytest.mark.asyncio
async def test_tls(a2a_https_url):
    assert a2a_https_url.startswith("https://")
    # self-signed cert, auto-generated per test
```

<details>
<summary><strong>All available fixtures</strong></summary>

| Fixture | Type | Description |
|---------|------|-------------|
| `a2a_server` | `DummyA2AServer` | Server on random port |
| `a2a_url` | `str` | `http://127.0.0.1:<port>` |
| `a2a_http` | `httpx.AsyncClient` | Client with `base_url` set |
| `a2a_https_server` | `DummyA2AServer` | TLS server (self-signed cert) |
| `a2a_https_url` | `str` | `https://127.0.0.1:<port>` |
| `a2a_https_http` | `httpx.AsyncClient` | TLS client (`verify=False`) |
| `webhook_receiver` | `WebhookReceiver` | Collects push notifications |

</details>

---

## Commands

Send a command keyword as the first word of your message:

| Command | Behavior | States |
|---------|----------|--------|
| `echo <text>` | Echoes text back | completed |
| `stream <text>` | Streams response in chunks (SSE) | working, completed |
| `ask` | Asks for input, completes on follow-up | input_required, completed |
| `slow` | Runs ~10s with progress updates | working, completed/canceled |
| `fail` | Transitions to FAILED with error | failed |
| `reject` | Immediately rejects | rejected |
| `auth` | Requires auth token, completes on follow-up | auth_required, completed |
| `file` | Returns a FilePart artifact | completed |
| `data` | Returns a DataPart (JSON) artifact | completed |
| `multi` | Returns 3 artifacts with chunked delivery | completed |
| `ext` | Exercises extension negotiation | completed |
| `ext-required` | Enforces required extension or returns -32008 | completed/error |
| `debug` | Returns request metadata (extended card only) | completed |
| `<anything>` | Falls back to echo | completed |

---

## Extensions

The dummy server implements A2A 1.0 extension negotiation for testing extension plugins.

### How it works

```
Client                                              Server
  |                                                    |
  |  POST / + X-A2A-Extensions: urn:a2a:dummy:...      |
  | -------------------------------------------------> |
  |                                                    | checks context.requested_extensions
  |                                                    | activates matching extensions
  |                                                    | tags artifacts with extension URIs
  |  Response + X-A2A-Extensions: urn:a2a:dummy:...    |
  | <------------------------------------------------- |
  |                                                    |
```

1. Agent card advertises extensions in `capabilities.extensions`
2. Client sends `X-A2A-Extensions` header with comma-separated URIs
3. Server activates recognized extensions, ignores unknown ones
4. Response header echoes which extensions were activated
5. Artifacts are tagged via `artifact.extensions`

### Registered extensions

| URI | Required | Params | What it does |
|-----|----------|--------|-------------|
| `urn:a2a:dummy:echo-metadata` | no | none | Reflects negotiation state in response artifact |
| `urn:a2a:dummy:timestamp` | no | `{"format": "iso8601"}` | Adds server timestamp to artifacts |
| `urn:a2a:dummy:trace-id` | no | none | Attaches a trace identifier to the response |
| `urn:a2a:dummy:priority` | no | `{"levels": "low,normal,high"}` | Acknowledges priority level in the response |
| `urn:a2a:dummy:locale` | no | none | Acknowledges locale preference in the response |
| `urn:a2a:dummy:required-test` | **yes** | none | Enforced by `ext-required`. Returns -32008 if missing |

Extension URIs are importable:

```python
from dummy_a2a.agent_card import (
    EXT_ECHO_METADATA, EXT_TIMESTAMP, EXT_TRACE_ID,
    EXT_PRIORITY, EXT_LOCALE, EXT_REQUIRED,
)
```

### Extension plugins

Register your own A2A extension with the dummy server using `A2APlugin`. The server will advertise it in the agent card, route its command to your handler, and the `ext` skill will activate it during header negotiation -- no changes to dummy-a2a needed.

An `A2APlugin` bundles four pieces:

| Field | Type | What it does |
|-------|------|-------------|
| `extension` | `AgentExtension` | Declared in `capabilities.extensions` on the agent card |
| `skill` | `AgentSkill` | Listed in `skills` on the agent card |
| `command` | `str` | First word of the user message that routes to your handler |
| `handler` | `SkillHandler` | Async handler that produces task events and artifacts |

**Minimal example:**

```python
from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    AgentExtension,
    AgentSkill,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from a2a.utils import new_text_artifact

from dummy_a2a import A2APlugin, DummyA2AServer

MY_EXT_URI = "urn:example:my-extension"


class MyExtensionSkill:
    async def handle(self, context: RequestContext, event_queue: EventQueue) -> None:
        # Activate the extension if requested via header
        if MY_EXT_URI in context.requested_extensions:
            context.add_activated_extension(MY_EXT_URI)

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
                artifact=new_text_artifact(name="result", text="hello from plugin"),
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


my_plugin = A2APlugin(
    extension=AgentExtension(
        uri=MY_EXT_URI,
        description="My custom A2A extension",
    ),
    skill=AgentSkill(
        id="myext",
        name="My Extension",
        description="Test skill for my extension.",
        tags=["test"],
        examples=["myext hello"],
        input_modes=["text/plain"],
        output_modes=["text/plain"],
    ),
    command="myext",
    handler=MyExtensionSkill(),
)
```

**Start the server with your plugin:**

```python
async with DummyA2AServer(port=0, extensions=[my_plugin]) as server:
    print(server.url)
    # Agent card now lists your extension and skill
    # "myext hello" routes to MyExtensionSkill
    # "ext" with X-A2A-Extensions header activates your extension
```

**Use in pytest:**

```python
import httpx
import pytest

from dummy_a2a import A2APlugin, DummyA2AServer

@pytest.fixture
async def server():
    async with DummyA2AServer(port=0, extensions=[my_plugin]) as s:
        yield s

@pytest.mark.asyncio
async def test_my_extension(server):
    async with httpx.AsyncClient(base_url=server.url) as client:
        # Verify extension is in the agent card
        card = (await client.get("/.well-known/agent-card.json")).json()
        uris = [e["uri"] for e in card["capabilities"]["extensions"]]
        assert MY_EXT_URI in uris

        # Send command with extension header
        resp = await client.post("/", json={
            "jsonrpc": "2.0", "id": 1,
            "method": "SendMessage",
            "params": {"message": {"messageId": "1", "role": 1,
                "parts": [{"text": "myext hello"}]}}
        }, headers={"X-A2A-Extensions": MY_EXT_URI})

        # Extension activated in response header
        assert MY_EXT_URI in resp.headers.get("X-A2A-Extensions", "")

        # Task completed
        task = resp.json()["result"]["task"]
        assert task["status"]["state"] == "TASK_STATE_COMPLETED"
```

**Multiple plugins:**

```python
async with DummyA2AServer(port=0, extensions=[plugin_a, plugin_b]) as server:
    ...
```

**Collision rules:**

- **Duplicate extension URIs** (between plugins or with built-ins) raise `ValueError` at startup.
- **Command collisions** with built-in skills log a warning and override the built-in.

**Public API for plugin authors:**

```python
from dummy_a2a import A2APlugin, SkillHandler, DummyA2AServer
```

`SkillHandler` is the protocol your handler must satisfy:

```python
class SkillHandler(Protocol):
    async def handle(self, context: RequestContext, event_queue: EventQueue) -> None: ...
```

### Testing extensions with curl

```bash
# Check what extensions the server supports
curl -s http://localhost:9000/.well-known/agent-card.json | jq '.capabilities.extensions'

# Negotiate extensions
curl -s http://localhost:9000/ \
  -H 'Content-Type: application/json' \
  -H 'X-A2A-Extensions: urn:a2a:dummy:echo-metadata, urn:a2a:dummy:timestamp' \
  -d '{"jsonrpc":"2.0","id":1,"method":"SendMessage","params":{"message":{"messageId":"1","role":1,"parts":[{"text":"ext"}]}}}' \
  -D - 2>/dev/null | head -20

# Test required extension enforcement (returns -32008)
curl -s http://localhost:9000/ \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"SendMessage","params":{"message":{"messageId":"1","role":1,"parts":[{"text":"ext-required"}]}}}'

# Satisfy the required extension
curl -s http://localhost:9000/ \
  -H 'Content-Type: application/json' \
  -H 'X-A2A-Extensions: urn:a2a:dummy:required-test' \
  -d '{"jsonrpc":"2.0","id":1,"method":"SendMessage","params":{"message":{"messageId":"1","role":1,"parts":[{"text":"ext-required"}]}}}'
```

### Testing extensions with pytest

```python
import httpx
import pytest

@pytest.mark.asyncio
async def test_extension_negotiation(a2a_url):
    async with httpx.AsyncClient(base_url=a2a_url) as client:
        resp = await client.post("/", json={
            "jsonrpc": "2.0", "id": 1,
            "method": "SendMessage",
            "params": {"message": {"messageId": "1", "role": 1,
                "parts": [{"text": "ext"}]}}
        }, headers={"X-A2A-Extensions": "urn:a2a:dummy:echo-metadata"})

        assert "urn:a2a:dummy:echo-metadata" in resp.headers["X-A2A-Extensions"]

        task = resp.json()["result"]["task"]
        assert "urn:a2a:dummy:echo-metadata" in task["artifacts"][0]["extensions"]

@pytest.mark.asyncio
async def test_required_extension_error(a2a_url):
    async with httpx.AsyncClient(base_url=a2a_url) as client:
        resp = await client.post("/", json={
            "jsonrpc": "2.0", "id": 1,
            "method": "SendMessage",
            "params": {"message": {"messageId": "1", "role": 1,
                "parts": [{"text": "ext-required"}]}}
        })
        assert resp.json()["error"]["code"] == -32008
```

### Testing extensions with portable contracts

```python
from dummy_a2a import verify_a2a_compliance

results = await verify_a2a_compliance(
    "http://localhost:9000",
    categories=["extensions"],
)
for r in results:
    print(f"{'PASS' if r.passed else 'FAIL'} {r.contract_id}")
```

---

## Contract Testing

46 portable contracts that verify A2A spec compliance against **any** server.

The dummy server is the reference implementation -- contracts are dogfooded against it in CI. Run them against your server to validate compliance.

### Run contracts against your server

Sequential execution against a shared server:

```python
import asyncio
from dummy_a2a import verify_a2a_compliance

async def main():
    results = await verify_a2a_compliance("http://localhost:9000")
    for r in results:
        print(f"{'PASS' if r.passed else 'FAIL'} {r.contract_id}: {r.detail}")

asyncio.run(main())
```

Concurrent execution with isolated servers (each contract gets a fresh instance):

```python
import asyncio
from contextlib import asynccontextmanager
from dummy_a2a import DummyA2AServer, verify_a2a_compliance

@asynccontextmanager
async def factory():
    async with DummyA2AServer(port=0) as server:
        yield server.url

async def main():
    results = await verify_a2a_compliance(server_factory=factory)
    for r in results:
        print(f"{'PASS' if r.passed else 'FAIL'} {r.contract_id}: {r.detail}")

asyncio.run(main())
```

### Run contracts as pytest

```python
import pytest
from dummy_a2a.contracts import a2a_contracts

@pytest.mark.asyncio
@pytest.mark.parametrize("contract", a2a_contracts, ids=lambda c: c.id)
async def test_a2a_compliance(contract):
    result = await contract.verify("http://localhost:9000")
    assert result.passed, f"{result.contract_id}: {result.detail}"
```

### Filter by category

```python
results = await verify_a2a_compliance(
    "http://localhost:9000",
    categories=["agent-card", "streaming", "extensions"],
)
```

Categories: `agent-card` `send-message` `task-state` `multi-turn` `get-task` `list-tasks` `cancel-task` `streaming` `subscribe-to-task` `content-types` `push-notifications` `errors` `extensions`

<details>
<summary><strong>All 46 contracts</strong></summary>

| ID | Category | What it checks |
|----|----------|---------------|
| `card.well-known` | agent-card | Card served at `/.well-known/agent-card.json` |
| `card.required-fields` | agent-card | Has name, description, version, skills, etc. |
| `card.skills-have-required-fields` | agent-card | Each skill has id, name, description, tags |
| `card.interface-protocol-version` | agent-card | Interface declares protocolVersion |
| `card.extended-card` | agent-card | Extended card via `GetExtendedAgentCard` |
| `send.completed` | send-message | SendMessage returns COMPLETED |
| `send.has-task-id` | send-message | Response has task ID and context ID |
| `send.has-artifacts` | send-message | Completed task has artifacts |
| `send.has-history` | send-message | Task includes message history |
| `state.failed` | task-state | FAILED state with error message |
| `state.rejected` | task-state | REJECTED state |
| `state.input-required` | task-state | INPUT_REQUIRED with prompt |
| `state.auth-required` | task-state | AUTH_REQUIRED with message |
| `multi-turn.input-required-follow-up` | multi-turn | Follow-up after INPUT_REQUIRED completes |
| `multi-turn.auth-required-follow-up` | multi-turn | Follow-up after AUTH_REQUIRED completes |
| `get-task.retrieves-task` | get-task | GetTask returns created task |
| `get-task.not-found` | get-task | GetTask errors on missing task |
| `get-task.includes-artifacts` | get-task | GetTask includes artifacts |
| `list-tasks.returns-tasks` | list-tasks | ListTasks returns created tasks |
| `cancel.cancels-task` | cancel-task | CancelTask transitions to CANCELED |
| `cancel.nonexistent-task` | cancel-task | CancelTask errors on missing task |
| `stream.sse-events` | streaming | SSE yields status + artifact events |
| `content.text-part` | content-types | TextPart artifact |
| `content.file-part` | content-types | FilePart with raw bytes |
| `content.data-part` | content-types | DataPart with structured JSON |
| `content.multi-artifact` | content-types | Multiple artifacts in one task |
| `push.create-config` | push-notifications | Create push notification config |
| `push.delete-config` | push-notifications | Delete push notification config |
| `push.get-config` | push-notifications | Retrieve a stored push notification config |
| `push.list-configs` | push-notifications | List push notification configs for a task |
| `subscribe.reattach` | subscribe-to-task | SubscribeToTask reattaches to a running task via SSE |
| `error.method-not-found` | errors | Unknown method returns -32601 |
| `error.invalid-jsonrpc` | errors | Invalid jsonrpc version returns error |
| `ext.card-advertises-extensions` | extensions | Card has extensions with uri + description |
| `ext.negotiation-activates` | extensions | Request header activates, response header confirms |
| `ext.unknown-ignored` | extensions | Unknown extension URIs don't error |
| `ext.artifact-tagged` | extensions | `artifact.extensions` contains activated URIs |
| `ext.multiple-extensions` | extensions | Multiple extensions activated simultaneously |
| `ext.params-in-card` | extensions | Extension params accessible in card |
| `ext.required-enforced` | extensions | Missing required extension returns -32008 |
| `ext.required-satisfied` | extensions | Providing required extension succeeds |
| `ext.partial-activation` | extensions | Only known extensions activate when mixed with unknown URIs |
| `ext.all-non-required` | extensions | All non-required extensions activate when requested together |
| `ext.artifact-extensions-exact` | extensions | `artifact.extensions` matches the activated set exactly |
| `ext.header-and-artifact-agree` | extensions | Response header and `artifact.extensions` agree |
| `ext.ordering-stable` | extensions | Same combination produces stable ordering across requests |

</details>

---

## Spec Coverage

| Area | Coverage |
|------|----------|
| **Operations** | 11/11 -- SendMessage, SendStreamingMessage, GetTask, ListTasks, CancelTask, SubscribeToTask, push notification CRUD (4), GetExtendedAgentCard |
| **Task states** | All 8 -- submitted, working, input_required, completed, canceled, failed, rejected, auth_required |
| **Content types** | TextPart, FilePart (raw bytes), DataPart (structured JSON) |
| **Extensions** | 6 test extensions + plugin system for external extensions, header negotiation, artifact tagging, required enforcement (-32008), extension params, multi-extension activation |
| **Agent card** | Public card (12 skills, 6 extensions), extended card (adds debug), streaming + push + extensions capabilities |

---

## Development

```bash
uv sync --dev
uv run pytest tests/ -v
uv run ruff check src/ tests/  # lint
uv run pyright                  # type check
```

---

## License

[Apache License 2.0](LICENSE)
