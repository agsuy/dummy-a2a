"""Tests for the multi-artifact skill."""

import pytest
from tests.helpers import send

pytestmark = pytest.mark.asyncio


async def test_multi_returns_completed(a2a_http):
    task = await send(a2a_http, "multi")
    assert task["status"]["state"] == "TASK_STATE_COMPLETED"


async def test_multi_returns_three_artifacts(a2a_http):
    task = await send(a2a_http, "multi")
    artifacts = task["artifacts"]
    assert len(artifacts) == 3


async def test_multi_artifact_names(a2a_http):
    task = await send(a2a_http, "multi")
    names = [a["name"] for a in task["artifacts"]]
    assert "artifact-1" in names
    assert "artifact-2" in names
    assert "artifact-3" in names


async def test_multi_first_artifact_is_text(a2a_http):
    task = await send(a2a_http, "multi")
    art1 = next(a for a in task["artifacts"] if a["name"] == "artifact-1")
    assert art1["parts"][0]["text"] == "First artifact content."


async def test_multi_third_artifact_is_data(a2a_http):
    task = await send(a2a_http, "multi")
    art3 = next(a for a in task["artifacts"] if a["name"] == "artifact-3")
    data = art3["parts"][0].get("data")
    assert data is not None
    assert data["artifact"] == "third"
