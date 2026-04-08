"""Internal utilities."""

from __future__ import annotations

import asyncio

import uvicorn


async def serve_with_signal(server: uvicorn.Server, started: asyncio.Event) -> None:
    """Run a uvicorn server and set *started* once the startup phase completes."""
    original_startup = server.startup

    async def _startup(*args: object, **kwargs: object) -> None:
        await original_startup(*args, **kwargs)  # type: ignore[arg-type]
        started.set()

    server.startup = _startup  # type: ignore[assignment]
    await server.serve()
