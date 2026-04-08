"""dummy-a2a: A programmable A2A test agent for spec compliance testing."""

__version__ = "0.3.0"

from dummy_a2a.contracts import a2a_contracts, verify_a2a_compliance
from dummy_a2a.server import DummyA2AServer

__all__ = ["DummyA2AServer", "a2a_contracts", "verify_a2a_compliance"]
