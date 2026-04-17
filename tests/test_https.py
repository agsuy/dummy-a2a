"""Tests for HTTPS/TLS support."""

import pytest

from tests.helpers import send

pytestmark = pytest.mark.asyncio


async def test_https_server_url_is_https(a2a_https_server):
    assert a2a_https_server.url.startswith("https://")


async def test_https_echo_works(a2a_https_http):
    task = await send(a2a_https_http, "echo hello tls")
    assert task["status"]["state"] == "TASK_STATE_COMPLETED"
    assert any("hello tls" in p.get("text", "") for a in task["artifacts"] for p in a["parts"])


async def test_https_card_url_is_https(a2a_https_server, a2a_https_http):
    resp = await a2a_https_http.get("/.well-known/agent-card.json")
    card_url = resp.json()["supportedInterfaces"][0]["url"]
    assert card_url.startswith("https://")
    assert card_url == a2a_https_server.url


async def test_https_agent_card(a2a_https_http):
    resp = await a2a_https_http.get("/.well-known/agent-card.json")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Dummy A2A Test Agent"
