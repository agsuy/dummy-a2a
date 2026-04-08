"""Tests for A2A error responses."""

import pytest

from tests.helpers import rpc_call

pytestmark = pytest.mark.asyncio


async def test_task_not_found_error(a2a_http):
    resp = await rpc_call(a2a_http, "GetTask", {"id": "does-not-exist"})
    assert "error" in resp


async def test_cancel_nonexistent_task(a2a_http):
    resp = await rpc_call(a2a_http, "CancelTask", {"id": "does-not-exist"})
    assert "error" in resp


async def test_invalid_jsonrpc_version(a2a_http):
    resp = await a2a_http.post(
        "/",
        json={"jsonrpc": "1.0", "id": 1, "method": "GetTask", "params": {"id": "x"}},
    )
    body = resp.json()
    assert "error" in body


async def test_method_not_found(a2a_http):
    resp = await rpc_call(a2a_http, "NonExistentMethod", {})
    assert "error" in resp
    assert resp["error"]["code"] == -32601  # Method not found
