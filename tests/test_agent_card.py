"""Tests for agent card and extended agent card."""

import pytest

from tests.helpers import rpc_call

pytestmark = pytest.mark.asyncio

_PUBLIC_SKILL_IDS = (
    "echo",
    "stream",
    "ask",
    "slow",
    "fail",
    "reject",
    "auth",
    "file",
    "data",
    "multi",
    "ext",
    "ext-required",
)


async def test_agent_card_served_at_well_known(a2a_http):
    resp = await a2a_http.get("/.well-known/agent-card.json")
    assert resp.status_code == 200
    card = resp.json()
    assert card["name"] == "Dummy A2A Test Agent"


async def test_agent_card_has_required_fields(a2a_http):
    resp = await a2a_http.get("/.well-known/agent-card.json")
    card = resp.json()
    assert "name" in card
    assert "description" in card
    assert "version" in card
    assert "skills" in card
    assert "capabilities" in card
    assert "supportedInterfaces" in card
    assert "defaultInputModes" in card
    assert "defaultOutputModes" in card


async def test_agent_card_lists_all_skills(a2a_http):
    resp = await a2a_http.get("/.well-known/agent-card.json")
    card = resp.json()
    skill_ids = [s["id"] for s in card["skills"]]
    for skill_id in _PUBLIC_SKILL_IDS:
        assert skill_id in skill_ids, f"Missing skill: {skill_id}"


async def test_agent_card_capabilities(a2a_http):
    resp = await a2a_http.get("/.well-known/agent-card.json")
    caps = resp.json()["capabilities"]
    assert caps.get("streaming") is True
    assert caps.get("pushNotifications") is True
    assert caps.get("extendedAgentCard") is True


async def test_skill_has_required_fields(a2a_http):
    resp = await a2a_http.get("/.well-known/agent-card.json")
    for skill in resp.json()["skills"]:
        assert "id" in skill
        assert "name" in skill
        assert "description" in skill
        assert "tags" in skill


async def test_public_card_does_not_include_debug(a2a_http):
    resp = await a2a_http.get("/.well-known/agent-card.json")
    skill_ids = [s["id"] for s in resp.json()["skills"]]
    assert "debug" not in skill_ids


async def test_extended_card_includes_debug_skill(a2a_http):
    resp = await rpc_call(a2a_http, "GetExtendedAgentCard", {})
    assert "result" in resp
    skill_ids = [s["id"] for s in resp["result"]["skills"]]
    assert "debug" in skill_ids
    # Should also have all public skills
    for sid in _PUBLIC_SKILL_IDS:
        assert sid in skill_ids


async def test_extended_card_has_all_required_fields(a2a_http):
    resp = await rpc_call(a2a_http, "GetExtendedAgentCard", {})
    card = resp["result"]
    assert "name" in card
    assert "version" in card
    assert "capabilities" in card
    assert "skills" in card


async def test_agent_card_interface_has_protocol_version(a2a_http):
    resp = await a2a_http.get("/.well-known/agent-card.json")
    interfaces = resp.json()["supportedInterfaces"]
    assert len(interfaces) >= 1
    iface = interfaces[0]
    assert iface["protocolBinding"] == "JSONRPC"
    assert iface["protocolVersion"] == "1.0"
