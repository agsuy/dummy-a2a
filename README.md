# dummy-a2a — A2A compliance in a box

[![CI](https://github.com/agsuy/dummy-a2a/actions/workflows/ci.yml/badge.svg)](https://github.com/agsuy/dummy-a2a/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/dummy-a2a.svg?logo=pypi&logoColor=white&label=version)](https://pypi.org/project/dummy-a2a/)
[![Python](https://img.shields.io/pypi/pyversions/dummy-a2a.svg?logo=python&logoColor=ffd43b&label=python)](https://pypi.org/project/dummy-a2a/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://github.com/agsuy/dummy-a2a/blob/main/LICENSE)

[![a2a-sdk latest on PyPI](https://img.shields.io/pypi/v/a2a-sdk.svg?logo=pypi&logoColor=white&label=a2a-sdk%20latest)](https://pypi.org/project/a2a-sdk/)
[![a2a-sdk pinned by dummy-a2a](https://img.shields.io/badge/a2a--sdk%20pin-1.0.1-informational)](https://github.com/agsuy/dummy-a2a/blob/main/pyproject.toml)

`dummy-a2a` is a programmable test agent for the [A2A protocol](https://google.github.io/A2A/). Send it a command keyword, get spec-compliant behavior back.
Every task state, every content type, every error code, every extension flow.

Ship it as a **test double** for your client, point its **46 portable contracts** at your server, or plug in your own extension and validate it end-to-end. One `pip install`, zero config.

### What you can validate

| Goal | How |
|------|-----|
| **Validate your client** | Point your client at the dummy server. Send commands (`echo`, `fail`, `stream`, `ask`, `ext`, ...) and assert your client handles each response shape, state transition, SSE stream, and error code correctly. |
| **Validate your server** | Run the 46 portable contracts against your server. Contracts are dogfooded against the dummy server in CI, so you know they're correct. |
| **Validate your extensions** | Register your extension as a plugin via `A2APlugin` and test it end-to-end: agent card advertising, header negotiation, artifact tagging, and multi-extension activation. |

```bash
pip install dummy-a2a
```

```python
async with DummyA2AServer(port=0) as server:
    # server.url → http://127.0.0.1:<random>
    # test your client against every A2A edge case
```

```python
# or validate any A2A server with portable contracts
results = await verify_a2a_compliance("http://your-server:9000")
```

> **~2 600 LOC · 11/11 operations · all 8 task states · 3 content types · 6 extensions + plugin system · 46 compliance contracts**

The `a2a-sdk pin` badge shows the version we test against.

Codebase is intentionally small and modular. Each skill is a self-contained file under 80 lines, each contract is an independent HTTP assertion. When the spec changes, the blast radius is typically one skill or one contract.

---

## Table of Contents

- [Install](#install)
- [Quick Start](#quick-start) -- get running in 30 seconds
  - [Standalone server](#1-standalone-server) (HTTP, HTTPS, Docker)
  - [As a library](#2-as-a-library)
  - [Pytest fixtures](#3-pytest-fixtures) (HTTP + HTTPS)
- [Commands](#commands) -- keyword-driven test behaviors
- [Contract Testing](#contract-testing) -- 46 portable compliance contracts
  - [Run against your server](#run-contracts-against-your-server)
  - [Run as pytest](#run-contracts-as-pytest)
  - [Contract list](#contract-list)
- [Extensions](#extensions) -- A2A 1.0 extension negotiation
  - [How it works](#how-it-works)
  - [Registered extensions](#registered-extensions)
  - [Testing with curl](#testing-extensions-with-curl)
  - [Testing with pytest](#testing-extensions-with-pytest)
  - [Testing with contracts](#testing-extensions-with-portable-contracts)
- [Development](#development)
- [License](#license)

---

## Install

From source:

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

Try it out:

```bash
# Agent card
curl http://localhost:9000/.well-known/agent-card.json
# → {"name": "Dummy A2A Test Agent", "skills": [...], "capabilities": {...}, ...}

# Send a message
curl -X POST http://localhost:9000/ \
  -H 'Content-Type: application/json' \
  -H 'A2A-Version: 1.0' \
  -d '{"jsonrpc":"2.0","id":1,"method":"SendMessage","params":{"message":{"messageId":"1","role":1,"parts":[{"text":"echo hello"}]}}}'
# → {"result": {"task": {"id": "...", "contextId": "...", "status": {"state": "TASK_STATE_COMPLETED"}, "artifacts": [{"parts": [{"text": "hello"}]}], "history": [...]}}, "id": 1, "jsonrpc": "2.0"}

# Trigger a failure
curl -X POST http://localhost:9000/ \
  -H 'Content-Type: application/json' \
  -H 'A2A-Version: 1.0' \
  -d '{"jsonrpc":"2.0","id":1,"method":"SendMessage","params":{"message":{"messageId":"1","role":1,"parts":[{"text":"fail"}]}}}'
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

# Silence SDK noise programmatically
async with DummyA2AServer(port=0, sdk_log_level="CRITICAL") as server:
    ...

# Verbose server + quiet SDK
async with DummyA2AServer(port=0, log_level="info", sdk_log_level="ERROR") as server:
    ...
```

### 3. Pytest fixtures

Drop this in your `conftest.py`:

```python
from dummy_a2a.testing import a2a_server, a2a_url, a2a_http  # noqa: F401
```

Write tests using the `a2a_http` fixture (an `httpx.AsyncClient` with `base_url` and `A2A-Version` already set):

```python
import pytest
from tests.helpers import send  # or write your own JSON-RPC helper

@pytest.mark.asyncio
async def test_echo(a2a_http):
    task = await send(a2a_http, "echo hello")
    assert task["status"]["state"] == "TASK_STATE_COMPLETED"

@pytest.mark.asyncio
async def test_failure(a2a_http):
    task = await send(a2a_http, "fail")
    assert task["status"]["state"] == "TASK_STATE_FAILED"
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
| `ext.negotiation-activates` | extensions | Requesting a known extension activates it (`artifact.extensions`) |
| `ext.unknown-ignored` | extensions | Unknown extension URIs don't error |
| `ext.artifact-tagged` | extensions | `artifact.extensions` contains activated URIs |
| `ext.multiple-extensions` | extensions | Multiple extensions activated simultaneously |
| `ext.params-in-card` | extensions | Extension params accessible in card |
| `ext.required-enforced` | extensions | Missing required extension returns -32008 |
| `ext.required-satisfied` | extensions | Providing required extension succeeds |
| `ext.partial-activation` | extensions | Only known extensions activate when mixed with unknown URIs |
| `ext.all-non-required` | extensions | All non-required extensions activate when requested together |
| `ext.artifact-extensions-exact` | extensions | `artifact.extensions` matches the activated set exactly |
| `ext.header-and-artifact-agree` | extensions | Activated extensions in artifact match the requested known extensions |
| `ext.ordering-stable` | extensions | Same combination produces stable ordering across requests |

</details>

---

## Extensions

The dummy server implements A2A 1.0 extension negotiation for testing extension plugins.

### How it works

```
Client                                              Server
  |                                                    |
  |  POST / + A2A-Extensions: urn:a2a:dummy:...      |
  | -------------------------------------------------> |
  |                                                    | checks context.requested_extensions
  |                                                    | activates matching extensions
  |                                                    | tags artifacts with extension URIs
  |  Response with artifact.extensions: [...]          |
  | <------------------------------------------------- |
  |                                                    |
```

1. Agent card advertises extensions in `capabilities.extensions`
2. Client sends `A2A-Extensions` header with comma-separated URIs
3. Server activates recognized extensions, ignores unknown ones
4. Activated extensions are listed in `artifact.extensions`

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

<details>
<summary><strong>Extension plugins — test your own extension</strong></summary>

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
from a2a.helpers import new_text_artifact

from dummy_a2a import A2APlugin, DummyA2AServer

MY_EXT_URI = "urn:example:my-extension"


class MyExtensionSkill:
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
    # "ext" with A2A-Extensions header activates your extension
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
    async with httpx.AsyncClient(
        base_url=server.url, headers={"A2A-Version": "1.0"},
    ) as client:
        # Verify extension is in the agent card
        card = (await client.get("/.well-known/agent-card.json")).json()
        uris = [e["uri"] for e in card["capabilities"]["extensions"]]
        assert MY_EXT_URI in uris

        # Plugin command routes to your handler
        resp = await client.post("/", json={
            "jsonrpc": "2.0", "id": 1,
            "method": "SendMessage",
            "params": {"message": {"messageId": "1", "role": 1,
                "parts": [{"text": "myext hello"}]}}
        })
        task = resp.json()["result"]["task"]
        assert task["status"]["state"] == "TASK_STATE_COMPLETED"

        # ext skill activates your extension during negotiation
        resp = await client.post("/", json={
            "jsonrpc": "2.0", "id": 2,
            "method": "SendMessage",
            "params": {"message": {"messageId": "2", "role": 1,
                "parts": [{"text": "ext"}]}}
        }, headers={"A2A-Extensions": MY_EXT_URI})
        task = resp.json()["result"]["task"]
        assert MY_EXT_URI in task["artifacts"][0].get("extensions", [])
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

</details>

### Testing extensions with curl

```bash
# Check what extensions the server supports
curl -s http://localhost:9000/.well-known/agent-card.json | jq '.capabilities.extensions'

# Negotiate extensions
curl -s http://localhost:9000/ \
  -H 'Content-Type: application/json' \
  -H 'A2A-Version: 1.0' \
  -H 'A2A-Extensions: urn:a2a:dummy:echo-metadata, urn:a2a:dummy:timestamp' \
  -d '{"jsonrpc":"2.0","id":1,"method":"SendMessage","params":{"message":{"messageId":"1","role":1,"parts":[{"text":"ext"}]}}}' \
  -D - 2>/dev/null | head -20

# Test required extension enforcement (returns -32008)
curl -s http://localhost:9000/ \
  -H 'Content-Type: application/json' \
  -H 'A2A-Version: 1.0' \
  -d '{"jsonrpc":"2.0","id":1,"method":"SendMessage","params":{"message":{"messageId":"1","role":1,"parts":[{"text":"ext-required"}]}}}'

# Satisfy the required extension
curl -s http://localhost:9000/ \
  -H 'Content-Type: application/json' \
  -H 'A2A-Version: 1.0' \
  -H 'A2A-Extensions: urn:a2a:dummy:required-test' \
  -d '{"jsonrpc":"2.0","id":1,"method":"SendMessage","params":{"message":{"messageId":"1","role":1,"parts":[{"text":"ext-required"}]}}}'
```

### Testing extensions with pytest

```python
import httpx
import pytest

@pytest.mark.asyncio
async def test_extension_negotiation(a2a_url):
    async with httpx.AsyncClient(
        base_url=a2a_url, headers={"A2A-Version": "1.0"},
    ) as client:
        resp = await client.post("/", json={
            "jsonrpc": "2.0", "id": 1,
            "method": "SendMessage",
            "params": {"message": {"messageId": "1", "role": 1,
                "parts": [{"text": "ext"}]}}
        }, headers={"A2A-Extensions": "urn:a2a:dummy:echo-metadata"})

        task = resp.json()["result"]["task"]
        assert "urn:a2a:dummy:echo-metadata" in task["artifacts"][0]["extensions"]

@pytest.mark.asyncio
async def test_required_extension_error(a2a_url):
    async with httpx.AsyncClient(
        base_url=a2a_url, headers={"A2A-Version": "1.0"},
    ) as client:
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

<<<<<<< HEAD
=======
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
| `ext.negotiation-activates` | extensions | Requesting a known extension activates it (`artifact.extensions`) |
| `ext.unknown-ignored` | extensions | Unknown extension URIs don't error |
| `ext.artifact-tagged` | extensions | `artifact.extensions` contains activated URIs |
| `ext.multiple-extensions` | extensions | Multiple extensions activated simultaneously |
| `ext.params-in-card` | extensions | Extension params accessible in card |
| `ext.required-enforced` | extensions | Missing required extension returns -32008 |
| `ext.required-satisfied` | extensions | Providing required extension succeeds |
| `ext.partial-activation` | extensions | Only known extensions activate when mixed with unknown URIs |
| `ext.all-non-required` | extensions | All non-required extensions activate when requested together |
| `ext.artifact-extensions-exact` | extensions | `artifact.extensions` matches the activated set exactly |
| `ext.header-and-artifact-agree` | extensions | Activated extensions in artifact match the requested known extensions |
| `ext.ordering-stable` | extensions | Same combination produces stable ordering across requests |

</details>

---

>>>>>>> 20abd93 (docs(readme): restructure intro and extensions section)
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
