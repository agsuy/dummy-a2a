"""Internal utilities."""

from __future__ import annotations

import asyncio

import uvicorn
from a2a.utils.constants import PROTOCOL_VERSION_1_0, VERSION_HEADER

# JSON-RPC clients must declare protocol 1.x; missing header defaults to 0.3 in the SDK.
A2A_JSONRPC_DEFAULT_HEADERS: dict[str, str] = {
    VERSION_HEADER: PROTOCOL_VERSION_1_0,
}


async def serve_with_signal(server: uvicorn.Server, started: asyncio.Event) -> None:
    """Run a uvicorn server and set *started* once the startup phase completes."""
    original_startup = server.startup

    async def _startup(*args: object, **kwargs: object) -> None:
        await original_startup(*args, **kwargs)  # type: ignore[arg-type]
        started.set()

    server.startup = _startup  # type: ignore[assignment]
    await server.serve()
