"""Tests for the multi-turn skill."""

import pytest

from tests.helpers import send

pytestmark = pytest.mark.asyncio


async def test_ask_returns_input_required(a2a_http):
    task = await send(a2a_http, "ask")
    assert task["status"]["state"] == "TASK_STATE_INPUT_REQUIRED"


async def test_ask_status_message_asks_question(a2a_http):
    task = await send(a2a_http, "ask")
    msg = task["status"].get("message")
    assert msg is not None
    assert "name" in msg["parts"][0]["text"].lower()


async def test_ask_follow_up_completes(a2a_http):
    task = await send(a2a_http, "ask")
    task_id = task["id"]
    assert task["status"]["state"] == "TASK_STATE_INPUT_REQUIRED"

    # Send follow-up with the task_id
    task2 = await send(a2a_http, "Claude", task_id=task_id)
    assert task2["status"]["state"] == "TASK_STATE_COMPLETED"
    assert len(task2["artifacts"]) == 1
    assert "Hello, Claude!" in task2["artifacts"][0]["parts"][0]["text"]
