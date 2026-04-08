"""Tests that all contracts pass against our own server (dogfood)."""

import pytest

from dummy_a2a import DummyA2AServer
from dummy_a2a.contracts import a2a_contracts, verify_a2a_compliance

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("contract", a2a_contracts, ids=lambda c: c.id)
async def test_contract(contract, a2a_url):
    result = await contract.verify(a2a_url)
    assert result.passed, f"{result.contract_id}: {result.detail}"


async def test_contracts_concurrent():
    """Run all contracts concurrently with isolated servers."""

    async def factory():
        async with DummyA2AServer(port=0) as server:
            yield server.url

    results = await verify_a2a_compliance(server_factory=factory)
    failed = [r for r in results if not r.passed]
    assert not failed, "\n".join(f"{r.contract_id}: {r.detail}" for r in failed)
