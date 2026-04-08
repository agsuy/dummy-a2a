"""Tests for the echo skill."""

import pytest
from tests.helpers import send

pytestmark = pytest.mark.asyncio


async def test_echo_returns_completed(a2a_http):
    task = await send(a2a_http, "echo hello world")
    assert task["status"]["state"] == "TASK_STATE_COMPLETED"


async def test_echo_artifact_contains_text(a2a_http):
    task = await send(a2a_http, "echo hello world")
    artifacts = task["artifacts"]
    assert len(artifacts) == 1
    assert artifacts[0]["name"] == "echo"
    assert artifacts[0]["parts"][0]["text"] == "hello world"


async def test_echo_has_history(a2a_http):
    task = await send(a2a_http, "echo test")
    history = task.get("history", [])
    assert len(history) >= 1
    assert history[0]["role"] == "ROLE_USER"
    assert history[0]["parts"][0]["text"] == "echo test"


async def test_echo_fallback_for_unknown_command(a2a_http):
    task = await send(a2a_http, "some unknown command")
    assert task["status"]["state"] == "TASK_STATE_COMPLETED"
    artifacts = task["artifacts"]
    assert len(artifacts) == 1
    # Falls back to echo, echoes the full text
    assert artifacts[0]["parts"][0]["text"] == "some unknown command"
