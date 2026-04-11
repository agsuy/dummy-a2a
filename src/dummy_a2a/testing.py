"""Reusable pytest fixtures for A2A spec compliance testing.

Import these fixtures into your conftest.py::

    from dummy_a2a.testing import a2a_server, a2a_client  # noqa: F401
"""

from __future__ import annotations

import asyncio
import ipaddress
import tempfile
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import httpx
import pytest_asyncio
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from dummy_a2a._utils import A2A_JSONRPC_DEFAULT_HEADERS, serve_with_signal
from dummy_a2a.server import DummyA2AServer


def _generate_self_signed_cert(tmpdir: Path) -> tuple[str, str]:
    """Generate a self-signed cert+key pair for testing. Returns (certfile, keyfile)."""
    import datetime

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1))
        .add_extension(
            x509.SubjectAlternativeName(
                [
                    x509.DNSName("localhost"),
                    x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                ]
            ),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    certfile = str(tmpdir / "cert.pem")
    keyfile = str(tmpdir / "key.pem")
    Path(certfile).write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    Path(keyfile).write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )
    return certfile, keyfile


class WebhookReceiver:
    """Collects push notifications sent to its endpoint."""

    def __init__(self) -> None:
        self.received: list[dict[str, Any]] = []
        self._host = "127.0.0.1"
        self._port = 0
        self._server: Any = None
        self._serve_task: asyncio.Task[None] | None = None
        self._started = asyncio.Event()

    @property
    def url(self) -> str:
        if self._server is None:
            raise RuntimeError("Webhook receiver not started")
        sockets = self._server.servers[0].sockets if self._server.servers else []
        if sockets:
            port = sockets[0].getsockname()[1]
        else:
            port = self._port
        return f"http://{self._host}:{port}/webhook"

    async def _handle(self, request: Request) -> JSONResponse:
        body = await request.json()
        self.received.append(body)
        return JSONResponse({"status": "ok"})

    async def start(self) -> None:
        import uvicorn

        app = Starlette(routes=[Route("/webhook", self._handle, methods=["POST"])])
        config = uvicorn.Config(app=app, host=self._host, port=self._port, log_level="warning")
        self._server = uvicorn.Server(config)
        self._serve_task = asyncio.create_task(serve_with_signal(self._server, self._started))
        await self._started.wait()

    async def stop(self) -> None:
        if self._server is not None:
            self._server.should_exit = True
        if self._serve_task is not None:
            await self._serve_task


# --- Fixtures ---


@pytest_asyncio.fixture
async def a2a_server() -> AsyncIterator[DummyA2AServer]:
    """Start a DummyA2AServer on a random port."""
    async with DummyA2AServer(port=0) as server:
        yield server


@pytest_asyncio.fixture
async def a2a_url(a2a_server: DummyA2AServer) -> str:
    """Base URL of the running test server."""
    return a2a_server.url


@pytest_asyncio.fixture
async def a2a_http(a2a_url: str) -> AsyncIterator[httpx.AsyncClient]:
    """HTTP client with base_url pointed at the test server."""
    async with httpx.AsyncClient(
        base_url=a2a_url,
        headers=A2A_JSONRPC_DEFAULT_HEADERS,
    ) as client:
        yield client


@pytest_asyncio.fixture
async def webhook_receiver() -> AsyncIterator[WebhookReceiver]:
    """Start a webhook receiver for push notification testing."""
    receiver = WebhookReceiver()
    await receiver.start()
    yield receiver
    await receiver.stop()


@pytest_asyncio.fixture
async def a2a_https_server() -> AsyncIterator[DummyA2AServer]:
    """Start a DummyA2AServer with TLS on a random port."""
    with tempfile.TemporaryDirectory() as tmpdir:
        certfile, keyfile = _generate_self_signed_cert(Path(tmpdir))
        async with DummyA2AServer(port=0, ssl_certfile=certfile, ssl_keyfile=keyfile) as server:
            yield server


@pytest_asyncio.fixture
async def a2a_https_url(a2a_https_server: DummyA2AServer) -> str:
    """Base URL of the running HTTPS test server."""
    return a2a_https_server.url


@pytest_asyncio.fixture
async def a2a_https_http(a2a_https_url: str) -> AsyncIterator[httpx.AsyncClient]:
    """HTTP client for the HTTPS test server (TLS verification disabled)."""
    async with httpx.AsyncClient(
        base_url=a2a_https_url,
        verify=False,
        headers=A2A_JSONRPC_DEFAULT_HEADERS,
    ) as client:
        yield client
