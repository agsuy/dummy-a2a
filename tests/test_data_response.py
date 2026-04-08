"""Tests for the data response skill."""

import pytest
from tests.helpers import send

pytestmark = pytest.mark.asyncio


async def test_data_returns_completed(a2a_http):
    task = await send(a2a_http, "data")
    assert task["status"]["state"] == "TASK_STATE_COMPLETED"


async def test_data_artifact_has_structured_json(a2a_http):
    task = await send(a2a_http, "data")
    artifacts = task["artifacts"]
    assert len(artifacts) == 1
    part = artifacts[0]["parts"][0]
    data = part.get("data")
    assert data is not None
    assert data["agent"] == "dummy-a2a"
    assert data["count"] == 42.0
    assert data["items"] == ["alpha", "beta", "gamma"]


async def test_data_artifact_media_type(a2a_http):
    task = await send(a2a_http, "data")
    part = task["artifacts"][0]["parts"][0]
    assert part.get("mediaType") == "application/json"
