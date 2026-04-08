"""Tests for the reject skill."""

import pytest

from tests.helpers import send

pytestmark = pytest.mark.asyncio


async def test_reject_returns_rejected_state(a2a_http):
    task = await send(a2a_http, "reject")
    assert task["status"]["state"] == "TASK_STATE_REJECTED"


async def test_reject_has_status_message(a2a_http):
    task = await send(a2a_http, "reject")
    msg = task["status"].get("message")
    assert msg is not None
    assert "rejected" in msg["parts"][0]["text"].lower()
