"""Tests for A2A extension support."""

import pytest

from dummy_a2a.agent_card import EXT_ECHO_METADATA, EXT_REQUIRED, EXT_TIMESTAMP
from tests.helpers import rpc_request, send_message_params

pytestmark = pytest.mark.asyncio

EXTENSION_HEADER = "X-A2A-Extensions"


async def test_ext_activates_requested_extensions(a2a_http):
    """Requesting known extensions activates them."""
    resp = await a2a_http.post(
        "/",
        json=rpc_request("SendMessage", send_message_params("ext")),
        headers={EXTENSION_HEADER: f"{EXT_ECHO_METADATA}, {EXT_TIMESTAMP}"},
    )
    assert resp.status_code == 200
    # Response header should echo activated extensions
    activated_header = resp.headers.get(EXTENSION_HEADER, "")
    assert EXT_ECHO_METADATA in activated_header
    assert EXT_TIMESTAMP in activated_header


async def test_ext_artifact_tagged_with_extensions(a2a_http):
    """Artifact.extensions contains activated extension URIs."""
    resp = await a2a_http.post(
        "/",
        json=rpc_request("SendMessage", send_message_params("ext")),
        headers={EXTENSION_HEADER: EXT_ECHO_METADATA},
    )
    task = resp.json()["result"]["task"]
    artifact = task["artifacts"][0]
    assert EXT_ECHO_METADATA in artifact.get("extensions", [])


async def test_ext_metadata_reflects_negotiation(a2a_http):
    """Ext skill returns accurate requested/activated lists."""
    resp = await a2a_http.post(
        "/",
        json=rpc_request("SendMessage", send_message_params("ext")),
        headers={EXTENSION_HEADER: f"{EXT_ECHO_METADATA}, {EXT_TIMESTAMP}"},
    )
    task = resp.json()["result"]["task"]
    data = task["artifacts"][0]["parts"][0]["data"]
    assert EXT_ECHO_METADATA in data["requested"]
    assert EXT_TIMESTAMP in data["requested"]
    assert EXT_ECHO_METADATA in data["activated"]
    assert EXT_TIMESTAMP in data["activated"]


async def test_ext_timestamp_included_when_activated(a2a_http):
    """Timestamp extension adds ISO 8601 timestamp."""
    resp = await a2a_http.post(
        "/",
        json=rpc_request("SendMessage", send_message_params("ext")),
        headers={EXTENSION_HEADER: EXT_TIMESTAMP},
    )
    task = resp.json()["result"]["task"]
    data = task["artifacts"][0]["parts"][0]["data"]
    assert "timestamp" in data


async def test_ext_unknown_extension_ignored(a2a_http):
    """Unknown extension URIs are ignored, no error."""
    resp = await a2a_http.post(
        "/",
        json=rpc_request("SendMessage", send_message_params("ext")),
        headers={EXTENSION_HEADER: "urn:a2a:unknown:extension"},
    )
    assert resp.status_code == 200
    task = resp.json()["result"]["task"]
    assert task["status"]["state"] == "TASK_STATE_COMPLETED"
    data = task["artifacts"][0]["parts"][0]["data"]
    assert "urn:a2a:unknown:extension" in data["requested"]
    assert not data.get("activated")


async def test_ext_no_extensions_header(a2a_http):
    """Ext skill works with no extensions header."""
    resp = await a2a_http.post(
        "/",
        json=rpc_request("SendMessage", send_message_params("ext")),
    )
    assert resp.status_code == 200
    task = resp.json()["result"]["task"]
    data = task["artifacts"][0]["parts"][0]["data"]
    assert not data.get("requested")
    assert not data.get("activated")


async def test_ext_required_missing_returns_error(a2a_http):
    """Missing required extension returns -32008."""
    resp = await a2a_http.post(
        "/",
        json=rpc_request("SendMessage", send_message_params("ext-required")),
    )
    body = resp.json()
    assert "error" in body
    assert body["error"]["code"] == -32008


async def test_ext_required_satisfied_completes(a2a_http):
    """Providing required extension completes normally."""
    resp = await a2a_http.post(
        "/",
        json=rpc_request("SendMessage", send_message_params("ext-required")),
        headers={EXTENSION_HEADER: EXT_REQUIRED},
    )
    body = resp.json()
    assert "result" in body
    task = body["result"]["task"]
    assert task["status"]["state"] == "TASK_STATE_COMPLETED"
    # Response header confirms activation
    assert EXT_REQUIRED in resp.headers.get(EXTENSION_HEADER, "")
    # Artifact tagged with extension
    assert EXT_REQUIRED in task["artifacts"][0].get("extensions", [])


async def test_card_advertises_extensions(a2a_http):
    """Agent card capabilities.extensions lists all test extensions."""
    resp = await a2a_http.get("/.well-known/agent-card.json")
    card = resp.json()
    exts = card["capabilities"].get("extensions", [])
    uris = [e["uri"] for e in exts]
    assert EXT_ECHO_METADATA in uris
    assert EXT_TIMESTAMP in uris
    assert EXT_REQUIRED in uris


async def test_card_extension_has_fields(a2a_http):
    """Each extension has uri and description."""
    resp = await a2a_http.get("/.well-known/agent-card.json")
    exts = resp.json()["capabilities"]["extensions"]
    for ext in exts:
        assert "uri" in ext
        assert "description" in ext


async def test_card_required_extension_flagged(a2a_http):
    """Required extension has required=true in the card."""
    resp = await a2a_http.get("/.well-known/agent-card.json")
    exts = resp.json()["capabilities"]["extensions"]
    required_ext = next(e for e in exts if e["uri"] == EXT_REQUIRED)
    assert required_ext.get("required") is True


async def test_card_extension_params(a2a_http):
    """Timestamp extension has params in the card."""
    resp = await a2a_http.get("/.well-known/agent-card.json")
    exts = resp.json()["capabilities"]["extensions"]
    ts_ext = next(e for e in exts if e["uri"] == EXT_TIMESTAMP)
    assert ts_ext.get("params", {}).get("format") == "iso8601"
