"""DummyA2AServer -- programmatic API for starting/stopping the test agent."""

from __future__ import annotations

import asyncio
import logging
from typing import Self

import httpx
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.context import ServerCallContext
from a2a.server.events import InMemoryQueueManager
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import (
    BasePushNotificationSender,
    InMemoryPushNotificationConfigStore,
    InMemoryTaskStore,
)
from a2a.types import AgentCard

from dummy_a2a._utils import serve_with_signal
from dummy_a2a.agent_card import build_agent_card, build_extended_agent_card
from dummy_a2a.executor import DummyAgentExecutor


class DummyA2AServer:
    """A programmable A2A test agent server.

    Usage::

        async with DummyA2AServer(port=0) as server:
            print(server.url)  # http://127.0.0.1:<random>
            # query it with any A2A client

    Args:
        host: Bind address. Defaults to "127.0.0.1".
        port: Bind port. Use 0 for a random available port.
        log_level: Logging level for the server (uvicorn) logger
            (e.g. ``"warning"``, ``"error"``). Defaults to ``"warning"``.
        sdk_log_level: Logging level for the ``a2a`` SDK logger
            (e.g. ``"WARNING"``, ``"ERROR"``). Defaults to ``None`` (inherit).
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 9000,
        ssl_keyfile: str | None = None,
        ssl_certfile: str | None = None,
        log_level: str = "warning",
        sdk_log_level: str | int | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._ssl_keyfile = ssl_keyfile
        self._ssl_certfile = ssl_certfile
        self._log_level = log_level
        self._sdk_log_level = sdk_log_level
        self._server: uvicorn.Server | None = None
        self._serve_task: asyncio.Task[None] | None = None
        self._started = asyncio.Event()
        self._agent_card: AgentCard | None = None
        self._extended_card: AgentCard | None = None

    @property
    def url(self) -> str:
        """Base URL of the running server."""
        if self._server is None or not self._started.is_set():
            raise RuntimeError("Server not started")
        # After startup, get the actual bound port (important when port=0)
        sockets = self._server.servers[0].sockets if self._server.servers else []
        if sockets:
            actual_port = sockets[0].getsockname()[1]
        else:
            actual_port = self._port
        scheme = "https" if self._ssl_certfile else "http"
        return f"{scheme}://{self._host}:{actual_port}"

    @property
    def agent_card(self) -> AgentCard:
        if self._agent_card is None:
            raise RuntimeError("Server not started")
        return self._agent_card

    async def start(self) -> None:
        """Start the server in the background."""
        # Disable sse-starlette's process-global shutdown flag.  It is shared
        # across all server instances in the same process: when one server
        # stops, the flag aborts SSE streams on every other server.  We
        # manage shutdown ourselves via ``uvicorn.Server.should_exit``.
        from sse_starlette.sse import AppStatus

        AppStatus.should_exit = False
        AppStatus.disable_automatic_graceful_drain()

        if self._sdk_log_level is not None:
            logging.getLogger("a2a").setLevel(self._sdk_log_level)

        if self._sdk_log_level is not None:
            logging.getLogger("a2a").setLevel(self._sdk_log_level)

        executor = DummyAgentExecutor()
        executor.register_all_skills()

        task_store = InMemoryTaskStore()
        queue_manager = InMemoryQueueManager()
        push_config_store = InMemoryPushNotificationConfigStore()
        push_sender = BasePushNotificationSender(
            httpx_client=httpx.AsyncClient(),
            config_store=push_config_store,
            context=ServerCallContext(),
        )
        handler = DefaultRequestHandler(
            agent_executor=executor,
            task_store=task_store,
            queue_manager=queue_manager,
            push_config_store=push_config_store,
            push_sender=push_sender,
        )

        self._agent_card = build_agent_card(self._host, self._port)
        self._extended_card = build_extended_agent_card(self._host, self._port)

        a2a_app = A2AStarletteApplication(
            agent_card=self._agent_card,
            http_handler=handler,
            extended_agent_card=self._extended_card,
        )
        app = a2a_app.build()

        config = uvicorn.Config(
            app=app,
            host=self._host,
            port=self._port,
            log_level=self._log_level,
            ssl_keyfile=self._ssl_keyfile,
            ssl_certfile=self._ssl_certfile,
        )
        self._server = uvicorn.Server(config)

        self._serve_task = asyncio.create_task(serve_with_signal(self._server, self._started))
        await self._started.wait()

    async def stop(self) -> None:
        """Stop the server gracefully."""
        if self._server is not None:
            self._server.should_exit = True
        if self._serve_task is not None:
            await self._serve_task
            self._serve_task = None

    async def __aenter__(self) -> Self:
        await self.start()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.stop()
