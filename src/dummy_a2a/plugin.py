"""Plugin dataclass for registering external A2A extensions with the dummy server."""

from dataclasses import dataclass

from a2a.types import AgentExtension, AgentSkill

from dummy_a2a.skills.base import SkillHandler


@dataclass(frozen=True)
class A2APlugin:
    """An external A2A extension plugin.

    Bundles the four pieces needed to register an extension with the dummy server:
    the agent card extension declaration, the agent card skill declaration,
    the command keyword that routes to the handler, and the handler itself.
    """

    extension: AgentExtension
    skill: AgentSkill
    command: str
    handler: SkillHandler
