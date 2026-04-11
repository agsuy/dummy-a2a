"""dummy-a2a: A programmable A2A test agent for spec compliance testing."""

__version__ = "0.6.0"

from dummy_a2a.contracts import a2a_contracts, verify_a2a_compliance
from dummy_a2a.plugin import A2APlugin
from dummy_a2a.server import DummyA2AServer
from dummy_a2a.skills.base import SkillHandler

__all__ = [
    "A2APlugin",
    "DummyA2AServer",
    "SkillHandler",
    "a2a_contracts",
    "verify_a2a_compliance",
]
