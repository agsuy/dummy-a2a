"""Test helpers for JSON-RPC calls."""

from __future__ import annotations

import uuid
from typing import Any

import httpx


def rpc_request(method: str, params: dict[str, Any], req_id: int = 1) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}


def send_message_params(text: str, task_id: str | None = None) -> dict[str, Any]:
    msg: dict[str, Any] = {
        "messageId": str(uuid.uuid4()),
        "role": 1,  # ROLE_USER
        "parts": [{"text": text}],
    }
    if task_id is not None:
        msg["taskId"] = task_id
    return {"message": msg}


async def send(client: httpx.AsyncClient, text: str, task_id: str | None = None) -> dict[str, Any]:
    """Send a message and return the result task dict."""
    resp = await client.post(
        "/",
        json=rpc_request("SendMessage", send_message_params(text, task_id=task_id)),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "result" in body, f"Expected result, got: {body}"
    return body["result"]["task"]


async def rpc_call(
    client: httpx.AsyncClient, method: str, params: dict[str, Any]
) -> dict[str, Any]:
    """Make a raw JSON-RPC call and return the full response body."""
    resp = await client.post("/", json=rpc_request(method, params))
    assert resp.status_code == 200
    return resp.json()
