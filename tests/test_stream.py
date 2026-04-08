"""Tests for the stream skill via SSE."""

import json

import httpx
import pytest

from tests.helpers import rpc_request, send, send_message_params

pytestmark = pytest.mark.asyncio


async def test_stream_blocking_returns_completed(a2a_http):
    """Non-streaming send still completes correctly."""
    task = await send(a2a_http, "stream hello")
    assert task["status"]["state"] == "TASK_STATE_COMPLETED"
    assert len(task["artifacts"]) >= 1


async def test_stream_sse_yields_events(a2a_url):
    """Streaming send yields SSE events with status and artifact updates."""
    events = []
    async with httpx.AsyncClient(base_url=a2a_url) as client:
        async with client.stream(
            "POST",
            "/",
            json=rpc_request("SendStreamingMessage", send_message_params("stream hello")),
        ) as resp:
            assert resp.status_code == 200
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    events.append(data)

    assert len(events) >= 2  # at least status updates + artifact events

    # Should have status updates and artifact updates
    status_events = [e for e in events if "statusUpdate" in e.get("result", {})]
    artifact_events = [e for e in events if "artifactUpdate" in e.get("result", {})]
    assert len(status_events) >= 2  # at least working + completed
    assert len(artifact_events) >= 1

    # Last status event should be completed
    last_status = status_events[-1]["result"]["statusUpdate"]["status"]
    assert last_status["state"] == "TASK_STATE_COMPLETED"
