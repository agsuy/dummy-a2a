# dummy-a2a

[![CI](https://github.com/agsuy/dummy-a2a/actions/workflows/ci.yml/badge.svg)](https://github.com/agsuy/dummy-a2a/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/dummy-a2a.svg?logo=pypi&logoColor=white&label=version)](https://pypi.org/project/dummy-a2a/)
[![Python](https://img.shields.io/pypi/pyversions/dummy-a2a.svg?logo=python&logoColor=ffd43b&label=python)](https://pypi.org/project/dummy-a2a/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://github.com/agsuy/dummy-a2a/blob/main/LICENSE)


A programmable A2A 1.0 test agent. Send it a command keyword, get spec-compliant behavior back.

Use it to **test your A2A client**, **validate spec compliance**, **test extension plugins**, or **run portable contracts** against any server.

Pinned to `a2a-sdk==1.0.0a0`. Covers **11/11 operations**, **all 8 task states**, **3 content types**, and **full extension negotiation**. We track the SDK and will update as new releases land.

### What you can validate

| Goal | How |
|------|-----|
| **Validate your client** | Point your client at the dummy server. Send commands (`echo`, `fail`, `stream`, `ask`, `ext`, ...) and assert your client handles each response shape, state transition, SSE stream, and error code correctly. |
| **Validate your server** | Run the 38 portable contracts against your server. Contracts are dogfooded against the dummy server in CI, so you know they're correct. |
| **Validate your extensions** | Test extension negotiation end-to-end: header negotiation, artifact tagging, required extension enforcement, and multi-extension activation. |

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
  - [Testing with curl](#testing-extensions-with-curl)
  - [Testing with pytest](#testing-extensions-with-pytest)
  - [Testing with contracts](#testing-extensions-with-portable-contracts)
- [Contract Testing](#contract-testing) -- 38 portable compliance contracts
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
| `urn:a2a:dummy:required-test` | **yes** | none | Enforced by `ext-required`. Returns -32008 if missing |

Extension URIs are importable:

```python
from dummy_a2a.agent_card import EXT_ECHO_METADATA, EXT_TIMESTAMP, EXT_REQUIRED
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

38 portable contracts that verify A2A spec compliance against **any** server.

The dummy server is the reference implementation -- contracts are dogfooded against it in CI. Run them against your server to validate compliance.

### Run contracts against your server

```python
import asyncio
from dummy_a2a import verify_a2a_compliance

async def main():
    results = await verify_a2a_compliance("http://localhost:9000")
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

Categories: `agent-card` `send-message` `task-state` `multi-turn` `get-task` `list-tasks` `cancel-task` `streaming` `content-types` `push-notifications` `errors` `extensions`

<details>
<summary><strong>All 38 contracts</strong></summary>

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

</details>

---

## Spec Coverage

| Area | Coverage |
|------|----------|
| **Operations** | 11/11 -- SendMessage, SendStreamingMessage, GetTask, ListTasks, CancelTask, SubscribeToTask, push notification CRUD (4), GetExtendedAgentCard |
| **Task states** | All 8 -- submitted, working, input_required, completed, canceled, failed, rejected, auth_required |
| **Content types** | TextPart, FilePart (raw bytes), DataPart (structured JSON) |
| **Extensions** | 3 test extensions, header negotiation, artifact tagging, required enforcement (-32008), extension params |
| **Agent card** | Public card (12 skills, 3 extensions), extended card (adds debug), streaming + push + extensions capabilities |

---

## Development

```bash
uv sync --dev
uv run pytest tests/ -v        # 104 tests
uv run ruff check src/ tests/  # lint
uv run pyright                  # type check
```

---

## License

[Apache License 2.0](LICENSE)
