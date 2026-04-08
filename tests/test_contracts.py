"""Tests that all contracts pass against our own server (dogfood)."""

import pytest

from dummy_a2a.contracts import a2a_contracts

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("contract", a2a_contracts, ids=lambda c: c.id)
async def test_contract(contract, a2a_url):
    result = await contract.verify(a2a_url)
    assert result.passed, f"{result.contract_id}: {result.detail}"
