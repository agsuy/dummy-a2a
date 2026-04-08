"""Tests for the debug skill."""

import pytest
from tests.helpers import send

pytestmark = pytest.mark.asyncio


async def test_debug_returns_completed(a2a_http):
    task = await send(a2a_http, "debug")
    assert task["status"]["state"] == "TASK_STATE_COMPLETED"


async def test_debug_returns_data_artifact(a2a_http):
    task = await send(a2a_http, "debug")
    artifacts = task["artifacts"]
    assert len(artifacts) == 1
    part = artifacts[0]["parts"][0]
    data = part.get("data")
    assert data is not None
    assert "task_id" in data
    assert "context_id" in data
    assert "user_input" in data
