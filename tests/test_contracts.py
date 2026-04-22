"""Tests that all contracts pass against our own server (dogfood)."""

from contextlib import asynccontextmanager

import pytest

from dummy_a2a import DummyA2AServer
from dummy_a2a.contracts import a2a_contracts, verify_a2a_compliance

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("contract", a2a_contracts, ids=lambda c: c.id)
async def test_contract(contract, a2a_url):
    result = await contract.verify(a2a_url)
    assert result.passed, f"{result.contract_id}: {result.detail}"


@pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning")
async def test_contracts_concurrent():
    """Run all contracts concurrently with isolated servers.

    The warning filter suppresses ActiveTask._run_consumer teardown races in
    the a2a-sdk that surface only under coverage + concurrent servers.
    Still present in a2a-sdk 1.0.1; remove once the SDK fixes cleanup.
    """

    @asynccontextmanager
    async def factory():
        async with DummyA2AServer(port=0) as server:
            yield server.url

    results = await verify_a2a_compliance(server_factory=factory)
    failed = [r for r in results if not r.passed]
    assert not failed, "\n".join(f"{r.contract_id}: {r.detail}" for r in failed)
