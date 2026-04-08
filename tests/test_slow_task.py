"""Tests for the slow task skill (cancel + get task)."""

import json

import pytest
from tests.helpers import rpc_call, rpc_request, send_message_params

pytestmark = pytest.mark.asyncio


async def test_slow_task_can_be_canceled(a2a_http):
    """Send slow task via streaming to get the task ID, then cancel it."""
    task_id = None
    async with a2a_http.stream(
        "POST",
        "/",
        json=rpc_request("SendStreamingMessage", send_message_params("slow")),
    ) as resp:
        async for line in resp.aiter_lines():
            if line.startswith("data: "):
                data = json.loads(line[6:])
                result = data.get("result", {})
                # taskId is in statusUpdate or artifactUpdate
                for key in ("statusUpdate", "artifactUpdate", "task"):
                    if key in result and "taskId" in result[key]:
                        task_id = result[key]["taskId"]
                        break
                if task_id:
                    break

    assert task_id is not None

    # Cancel the task
    cancel_resp = await rpc_call(a2a_http, "CancelTask", {"id": task_id})
    assert "result" in cancel_resp
    assert cancel_resp["result"]["status"]["state"] == "TASK_STATE_CANCELED"
