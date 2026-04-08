"""Tests for GetTask operation."""

import pytest
from tests.helpers import rpc_call, send

pytestmark = pytest.mark.asyncio


async def test_get_task_returns_task(a2a_http):
    task = await send(a2a_http, "echo hello")
    task_id = task["id"]

    resp = await rpc_call(a2a_http, "GetTask", {"id": task_id})
    assert "result" in resp
    retrieved = resp["result"]
    assert retrieved["id"] == task_id
    assert retrieved["status"]["state"] == "TASK_STATE_COMPLETED"


async def test_get_task_not_found(a2a_http):
    resp = await rpc_call(a2a_http, "GetTask", {"id": "nonexistent-task-id"})
    assert "error" in resp
    error = resp["error"]
    assert error["code"] < 0  # JSON-RPC error


async def test_get_task_includes_artifacts(a2a_http):
    task = await send(a2a_http, "echo hello")
    task_id = task["id"]

    resp = await rpc_call(a2a_http, "GetTask", {"id": task_id})
    retrieved = resp["result"]
    assert len(retrieved.get("artifacts", [])) == 1
    assert retrieved["artifacts"][0]["parts"][0]["text"] == "hello"
