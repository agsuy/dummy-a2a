"""Tests for ListTasks operation."""

import pytest

from tests.helpers import rpc_call, send

pytestmark = pytest.mark.asyncio


async def test_list_tasks_returns_created_tasks(a2a_http):
    await send(a2a_http, "echo one")
    await send(a2a_http, "echo two")

    resp = await rpc_call(a2a_http, "ListTasks", {})
    assert "result" in resp
    tasks = resp["result"]["tasks"]
    assert len(tasks) >= 2


async def test_list_tasks_empty_when_no_tasks(a2a_http):
    resp = await rpc_call(a2a_http, "ListTasks", {})
    assert "result" in resp
    tasks = resp["result"]["tasks"]
    assert len(tasks) == 0


async def test_list_tasks_includes_failed_tasks(a2a_http):
    await send(a2a_http, "echo ok")
    await send(a2a_http, "fail")

    resp = await rpc_call(a2a_http, "ListTasks", {})
    tasks = resp["result"]["tasks"]
    states = [t["status"]["state"] for t in tasks]
    assert "TASK_STATE_COMPLETED" in states
    assert "TASK_STATE_FAILED" in states
