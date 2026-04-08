"""Tests for the auth required skill."""

import pytest
from tests.helpers import send

pytestmark = pytest.mark.asyncio


async def test_auth_returns_auth_required(a2a_http):
    task = await send(a2a_http, "auth")
    assert task["status"]["state"] == "TASK_STATE_AUTH_REQUIRED"


async def test_auth_status_message_requests_token(a2a_http):
    task = await send(a2a_http, "auth")
    msg = task["status"].get("message")
    assert msg is not None
    assert "token" in msg["parts"][0]["text"].lower()


async def test_auth_follow_up_with_token_completes(a2a_http):
    task = await send(a2a_http, "auth")
    task_id = task["id"]
    assert task["status"]["state"] == "TASK_STATE_AUTH_REQUIRED"

    task2 = await send(a2a_http, "my-secret-token", task_id=task_id)
    assert task2["status"]["state"] == "TASK_STATE_COMPLETED"
    assert len(task2["artifacts"]) == 1
    assert "my-secret-token" in task2["artifacts"][0]["parts"][0]["text"]
