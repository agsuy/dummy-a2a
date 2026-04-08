"""Tests for the file response skill."""

import pytest

from tests.helpers import send

pytestmark = pytest.mark.asyncio


async def test_file_returns_completed(a2a_http):
    task = await send(a2a_http, "file")
    assert task["status"]["state"] == "TASK_STATE_COMPLETED"


async def test_file_artifact_has_raw_bytes(a2a_http):
    task = await send(a2a_http, "file")
    artifacts = task["artifacts"]
    assert len(artifacts) == 1
    part = artifacts[0]["parts"][0]
    assert part.get("filename") == "test.txt"
    assert part.get("mediaType") == "text/plain"
    # raw bytes are base64 encoded in JSON
    assert "raw" in part
