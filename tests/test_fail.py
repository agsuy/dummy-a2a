"""Tests for the fail skill."""

import pytest

from tests.helpers import send

pytestmark = pytest.mark.asyncio


async def test_fail_returns_failed_state(a2a_http):
    task = await send(a2a_http, "fail")
    assert task["status"]["state"] == "TASK_STATE_FAILED"


async def test_fail_has_status_message(a2a_http):
    task = await send(a2a_http, "fail")
    msg = task["status"].get("message")
    assert msg is not None
    assert "failure" in msg["parts"][0]["text"].lower()
