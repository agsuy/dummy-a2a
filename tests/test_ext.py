"""Tests for A2A extension support."""

import pytest

from dummy_a2a.agent_card import (
    EXT_ECHO_METADATA,
    EXT_LOCALE,
    EXT_PRIORITY,
    EXT_REQUIRED,
    EXT_TIMESTAMP,
    EXT_TRACE_ID,
)
from tests.helpers import rpc_request, send_message_params

pytestmark = pytest.mark.asyncio

EXTENSION_HEADER = "A2A-Extensions"


async def test_ext_activates_requested_extensions(a2a_http):
    """Requesting known extensions activates them."""
    resp = await a2a_http.post(
        "/",
        json=rpc_request("SendMessage", send_message_params("ext")),
        headers={EXTENSION_HEADER: f"{EXT_ECHO_METADATA}, {EXT_TIMESTAMP}"},
    )
    assert resp.status_code == 200
    task = resp.json()["result"]["task"]
    artifact_exts = task["artifacts"][0].get("extensions", [])
    assert EXT_ECHO_METADATA in artifact_exts
    assert EXT_TIMESTAMP in artifact_exts


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


# --- Multi-extension tests ---

ALL_NON_REQUIRED = [EXT_ECHO_METADATA, EXT_TIMESTAMP, EXT_TRACE_ID, EXT_PRIORITY, EXT_LOCALE]


async def test_ext_activates_three_plus_extensions(a2a_http):
    """All 5 non-required extensions activate when requested together."""
    resp = await a2a_http.post(
        "/",
        json=rpc_request("SendMessage", send_message_params("ext")),
        headers={EXTENSION_HEADER: ", ".join(ALL_NON_REQUIRED)},
    )
    assert resp.status_code == 200
    task = resp.json()["result"]["task"]
    artifact_exts = task["artifacts"][0].get("extensions", [])
    for uri in ALL_NON_REQUIRED:
        assert uri in artifact_exts, f"Expected {uri} in artifact extensions"


async def test_ext_partial_activation_mixed(a2a_http):
    """Only known extensions activate when mixed with unknown URIs."""
    known = [EXT_ECHO_METADATA, EXT_TRACE_ID]
    unknown = ["urn:a2a:unknown:one", "urn:a2a:unknown:two"]
    resp = await a2a_http.post(
        "/",
        json=rpc_request("SendMessage", send_message_params("ext")),
        headers={EXTENSION_HEADER: ", ".join(known + unknown)},
    )
    task = resp.json()["result"]["task"]
    data = task["artifacts"][0]["parts"][0]["data"]
    activated = data.get("activated", [])
    assert len(activated) == len(known)
    for uri in known:
        assert uri in activated
    for uri in unknown:
        assert uri not in activated


async def test_ext_artifact_extensions_exact_match(a2a_http):
    """artifact.extensions matches the activated set exactly (no extras, no missing)."""
    requested = [EXT_ECHO_METADATA, EXT_TRACE_ID, EXT_LOCALE]
    resp = await a2a_http.post(
        "/",
        json=rpc_request("SendMessage", send_message_params("ext")),
        headers={EXTENSION_HEADER: ", ".join(requested)},
    )
    task = resp.json()["result"]["task"]
    artifact_exts = set(task["artifacts"][0].get("extensions", []))
    assert artifact_exts == set(requested), (
        f"artifact.extensions {artifact_exts} != requested {set(requested)}"
    )


async def test_ext_activated_matches_requested(a2a_http):
    """Activated extensions in artifact match the known requested extensions."""
    requested = [EXT_ECHO_METADATA, EXT_PRIORITY]
    resp = await a2a_http.post(
        "/",
        json=rpc_request("SendMessage", send_message_params("ext")),
        headers={EXTENSION_HEADER: ", ".join(requested)},
    )
    task = resp.json()["result"]["task"]
    artifact_exts = set(task["artifacts"][0].get("extensions", []))
    assert artifact_exts == set(requested), (
        f"Artifact {artifact_exts} != requested {set(requested)}"
    )


async def test_ext_ordering_stable(a2a_http):
    """Same extension combination produces stable ordering across requests."""
    requested = [EXT_LOCALE, EXT_ECHO_METADATA, EXT_TRACE_ID]
    resp1 = await a2a_http.post(
        "/",
        json=rpc_request("SendMessage", send_message_params("ext")),
        headers={EXTENSION_HEADER: ", ".join(requested)},
    )
    resp2 = await a2a_http.post(
        "/",
        json=rpc_request("SendMessage", send_message_params("ext")),
        headers={EXTENSION_HEADER: ", ".join(requested)},
    )
    exts1 = resp1.json()["result"]["task"]["artifacts"][0].get("extensions", [])
    exts2 = resp2.json()["result"]["task"]["artifacts"][0].get("extensions", [])
    assert exts1 == exts2, f"Ordering unstable: {exts1} != {exts2}"


async def test_card_advertises_new_extensions(a2a_http):
    """Agent card includes the new trace-id, priority, and locale extensions."""
    resp = await a2a_http.get("/.well-known/agent-card.json")
    uris = [e["uri"] for e in resp.json()["capabilities"]["extensions"]]
    assert EXT_TRACE_ID in uris
    assert EXT_PRIORITY in uris
    assert EXT_LOCALE in uris


async def test_ext_priority_has_params(a2a_http):
    """Priority extension has params.levels in the agent card."""
    resp = await a2a_http.get("/.well-known/agent-card.json")
    exts = resp.json()["capabilities"]["extensions"]
    priority_ext = next(e for e in exts if e["uri"] == EXT_PRIORITY)
    assert priority_ext.get("params", {}).get("levels") == "low,normal,high"
