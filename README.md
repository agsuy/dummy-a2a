# dummy-a2a

A programmable A2A 1.0 test agent. Send it a command keyword, get spec-compliant behavior back.

Use it to **test your A2A client**, **validate spec compliance**, or **run portable contracts** against any server.

Pinned to `a2a-sdk==1.0.0a0`.

---

## Install

```bash
pip install dummy-a2a

# or from source
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

Then hit it:

```bash
# Agent card
curl http://localhost:9000/.well-known/agent-card.json

# Send a message
curl -X POST http://localhost:9000/ -H 'Content-Type: application/json' -d '{
  "jsonrpc": "2.0", "id": 1,
  "method": "SendMessage",
  "params": {"message": {"messageId": "1", "role": 1, "parts": [{"text": "echo hello"}]}}
}'
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
async def test_my_client_handles_echo(a2a_url):
    result = await my_a2a_client.send(a2a_url, "echo hello")
    assert result.state == "TASK_STATE_COMPLETED"

@pytest.mark.asyncio
async def test_my_client_handles_failure(a2a_url):
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

#### Available fixtures

| Fixture | Type | Description |
|---------|------|-------------|
| `a2a_server` | `DummyA2AServer` | Server on random port |
| `a2a_url` | `str` | `http://127.0.0.1:<port>` |
| `a2a_http` | `httpx.AsyncClient` | Client with `base_url` set |
| `a2a_https_server` | `DummyA2AServer` | TLS server (self-signed cert) |
| `a2a_https_url` | `str` | `https://127.0.0.1:<port>` |
| `a2a_https_http` | `httpx.AsyncClient` | TLS client (`verify=False`) |
| `webhook_receiver` | `WebhookReceiver` | Collects push notifications |

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
| `debug` | Returns request metadata (extended card only) | completed |
| `<anything>` | Falls back to echo | completed |

---

## Contract Testing

30 portable contracts that verify A2A spec compliance against **any** server.

The dummy server is the reference implementation. Contracts pass against it (dogfooded in CI), so you know the contracts themselves are correct. Then run them against your server.

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
    categories=["agent-card", "streaming", "errors"],
)
```

Categories: `agent-card`, `send-message`, `task-state`, `multi-turn`, `get-task`, `list-tasks`, `cancel-task`, `streaming`, `content-types`, `push-notifications`, `errors`.

### Contract list

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

---

## Spec Coverage

### Operations (11/11)

SendMessage, SendStreamingMessage, GetTask, ListTasks, CancelTask, SubscribeToTask, CreateTaskPushNotificationConfig, GetTaskPushNotificationConfig, ListTaskPushNotificationConfigs, DeleteTaskPushNotificationConfig, GetExtendedAgentCard

### All 8 task states

submitted, working, input_required, completed, canceled, failed, rejected, auth_required

### Content types

TextPart, FilePart (raw bytes), DataPart (structured JSON)

### Agent card

- Public card at `/.well-known/agent-card.json` (10 skills)
- Extended card via `GetExtendedAgentCard` (adds debug skill)
- Capabilities: streaming, push notifications, extended agent card

---

## Development

```bash
uv sync --dev
uv run pytest tests/ -v        # 84 tests
uv run ruff check src/ tests/  # lint
uv run pyright                  # type check
```

## License

[Apache License 2.0](LICENSE)
