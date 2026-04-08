"""Tests for push notification config CRUD."""

import pytest
from tests.helpers import rpc_call, send

pytestmark = pytest.mark.asyncio


async def test_set_push_notification_config(a2a_http, webhook_receiver):
    task = await send(a2a_http, "echo hello")
    task_id = task["id"]

    resp = await rpc_call(
        a2a_http,
        "CreateTaskPushNotificationConfig",
        {
            "taskId": task_id,
            "url": webhook_receiver.url,
        },
    )
    assert "result" in resp, f"Expected result, got: {resp}"


async def test_get_push_notification_config(a2a_http, webhook_receiver):
    task = await send(a2a_http, "echo hello")
    task_id = task["id"]

    # Create
    create_resp = await rpc_call(
        a2a_http,
        "CreateTaskPushNotificationConfig",
        {
            "taskId": task_id,
            "url": webhook_receiver.url,
        },
    )
    config = create_resp["result"]
    config_id = config.get("id")

    # Get
    if config_id:
        get_resp = await rpc_call(
            a2a_http,
            "GetTaskPushNotificationConfig",
            {"taskId": task_id, "id": config_id},
        )
        assert "result" in get_resp


async def test_delete_push_notification_config(a2a_http, webhook_receiver):
    task = await send(a2a_http, "echo hello")
    task_id = task["id"]

    create_resp = await rpc_call(
        a2a_http,
        "CreateTaskPushNotificationConfig",
        {
            "taskId": task_id,
            "url": webhook_receiver.url,
        },
    )
    config = create_resp["result"]
    config_id = config.get("id")

    if config_id:
        del_resp = await rpc_call(
            a2a_http,
            "DeleteTaskPushNotificationConfig",
            {"taskId": task_id, "id": config_id},
        )
        assert "error" not in del_resp
