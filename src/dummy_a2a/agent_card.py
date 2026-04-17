"""Agent card definitions for the dummy A2A test agent."""

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentExtension,
    AgentInterface,
    AgentProvider,
    AgentSkill,
)

# Extension URIs — importable by tests/contracts
EXT_ECHO_METADATA = "urn:a2a:dummy:echo-metadata"
EXT_TIMESTAMP = "urn:a2a:dummy:timestamp"
EXT_TRACE_ID = "urn:a2a:dummy:trace-id"
EXT_PRIORITY = "urn:a2a:dummy:priority"
EXT_LOCALE = "urn:a2a:dummy:locale"
EXT_REQUIRED = "urn:a2a:dummy:required-test"

EXTENSIONS: list[AgentExtension] = [
    AgentExtension(
        uri=EXT_ECHO_METADATA,
        description=(
            "When activated, reflects extension negotiation state in the response artifact."
        ),
    ),
    AgentExtension(
        uri=EXT_TIMESTAMP,
        description="When activated, adds a server timestamp to artifacts.",
        params={"format": "iso8601"},
    ),
    AgentExtension(
        uri=EXT_TRACE_ID,
        description="When activated, attaches a trace identifier to the response.",
    ),
    AgentExtension(
        uri=EXT_PRIORITY,
        description="When activated, acknowledges priority level in the response.",
        params={"levels": "low,normal,high"},
    ),
    AgentExtension(
        uri=EXT_LOCALE,
        description="When activated, acknowledges locale preference in the response.",
    ),
    AgentExtension(
        uri=EXT_REQUIRED,
        description=(
            "Test extension marked as required. The 'ext-required' command returns -32008 "
            "if this extension is not requested."
        ),
        required=True,
    ),
]

SKILLS: list[AgentSkill] = [
    AgentSkill(
        id="echo",
        name="Echo",
        description="Echoes back the user's input text as an artifact.",
        tags=["test", "echo"],
        examples=["echo hello world"],
        input_modes=["text/plain"],
        output_modes=["text/plain"],
    ),
    AgentSkill(
        id="stream",
        name="Stream",
        description="Responds with streaming chunked text, demonstrating SSE artifact delivery.",
        tags=["test", "stream"],
        examples=["stream hello world"],
        input_modes=["text/plain"],
        output_modes=["text/plain"],
    ),
    AgentSkill(
        id="ask",
        name="Multi-Turn",
        description=(
            "Asks a follow-up question (input_required), then completes on the second turn."
        ),
        tags=["test", "multi-turn", "input-required"],
        examples=["ask"],
        input_modes=["text/plain"],
        output_modes=["text/plain"],
    ),
    AgentSkill(
        id="slow",
        name="Slow Task",
        description=(
            "Runs for ~10 seconds with progress updates. Useful for testing cancel and resubscribe."
        ),
        tags=["test", "slow", "cancel", "resubscribe"],
        examples=["slow"],
        input_modes=["text/plain"],
        output_modes=["text/plain"],
    ),
    AgentSkill(
        id="fail",
        name="Fail",
        description="Transitions to FAILED state with an error message.",
        tags=["test", "fail", "error"],
        examples=["fail"],
        input_modes=["text/plain"],
        output_modes=["text/plain"],
    ),
    AgentSkill(
        id="reject",
        name="Reject",
        description="Immediately rejects the task with REJECTED state.",
        tags=["test", "reject"],
        examples=["reject"],
        input_modes=["text/plain"],
        output_modes=["text/plain"],
    ),
    AgentSkill(
        id="auth",
        name="Auth Required",
        description="Transitions to AUTH_REQUIRED, then completes when credentials are provided.",
        tags=["test", "auth", "auth-required"],
        examples=["auth"],
        input_modes=["text/plain"],
        output_modes=["text/plain"],
    ),
    AgentSkill(
        id="file",
        name="File Response",
        description="Returns a file artifact with raw bytes.",
        tags=["test", "file", "binary"],
        examples=["file"],
        input_modes=["text/plain"],
        output_modes=["application/octet-stream", "text/plain"],
    ),
    AgentSkill(
        id="data",
        name="Data Response",
        description="Returns a structured JSON data artifact.",
        tags=["test", "data", "json"],
        examples=["data"],
        input_modes=["text/plain"],
        output_modes=["application/json"],
    ),
    AgentSkill(
        id="multi",
        name="Multi-Artifact",
        description="Returns multiple artifacts, including chunked delivery with append/lastChunk.",
        tags=["test", "multi-artifact", "chunked"],
        examples=["multi"],
        input_modes=["text/plain"],
        output_modes=["text/plain", "application/json"],
    ),
    AgentSkill(
        id="ext",
        name="Extension Test",
        description=(
            "Exercises A2A extension negotiation. Activates requested extensions and returns "
            "metadata."
        ),
        tags=["test", "extension"],
        examples=["ext"],
        input_modes=["text/plain"],
        output_modes=["application/json"],
    ),
    AgentSkill(
        id="ext-required",
        name="Required Extension Test",
        description=(
            "Tests required extension enforcement. Returns -32008 if "
            "urn:a2a:dummy:required-test is not in X-A2A-Extensions header."
        ),
        tags=["test", "extension", "required"],
        examples=["ext-required"],
        input_modes=["text/plain"],
        output_modes=["application/json"],
    ),
]

DEBUG_SKILL = AgentSkill(
    id="debug",
    name="Debug",
    description="Returns internal server state for debugging. Only available via extended card.",
    tags=["debug", "admin"],
    examples=["debug"],
    input_modes=["text/plain"],
    output_modes=["application/json"],
)


def build_agent_card(
    host: str,
    port: int,
    *,
    extra_skills: list[AgentSkill] | None = None,
    extra_extensions: list[AgentExtension] | None = None,
) -> AgentCard:
    """Build an agent card, optionally with extra skills/extensions appended."""
    skills = SKILLS if extra_skills is None else SKILLS + extra_skills
    extensions = EXTENSIONS if extra_extensions is None else EXTENSIONS + extra_extensions
    return AgentCard(
        name="Dummy A2A Test Agent",
        description=(
            "A programmable A2A test agent that exercises every protocol feature. "
            "Send a command keyword to trigger specific spec behaviors."
        ),
        version="1.0.0",
        provider=AgentProvider(organization="dummy-a2a"),
        supported_interfaces=[
            AgentInterface(
                url=f"http://{host}:{port}",
                protocol_binding="JSONRPC",
                protocol_version="1.0",
            ),
        ],
        capabilities=AgentCapabilities(
            streaming=True,
            push_notifications=True,
            extended_agent_card=True,
            extensions=extensions,
        ),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=skills,
    )


def build_extended_agent_card(
    host: str,
    port: int,
    *,
    extra_skills: list[AgentSkill] | None = None,
    extra_extensions: list[AgentExtension] | None = None,
) -> AgentCard:
    """Build the extended agent card (includes debug skill)."""
    return build_agent_card(
        host,
        port,
        extra_skills=[DEBUG_SKILL] + (extra_skills or []),
        extra_extensions=extra_extensions,
    )
