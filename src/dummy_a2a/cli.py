"""CLI entry point for the dummy A2A test agent."""

import argparse
import asyncio

from dummy_a2a.server import DummyA2AServer


def main() -> None:
    parser = argparse.ArgumentParser(description="Dummy A2A Test Agent")
    parser.add_argument("--host", default="0.0.0.0", help="Bind address (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=9000, help="Bind port (default: 9000)")
    parser.add_argument("--ssl-keyfile", default=None, help="SSL key file for HTTPS")
    parser.add_argument("--ssl-certfile", default=None, help="SSL certificate file for HTTPS")
    args = parser.parse_args()

    async def run() -> None:
        async with DummyA2AServer(
            host=args.host,
            port=args.port,
            ssl_keyfile=args.ssl_keyfile,
            ssl_certfile=args.ssl_certfile,
        ) as server:
            print(f"Dummy A2A agent running at {server.url}")
            print(f"Agent card: {server.url}/.well-known/agent-card.json")
            print("Press Ctrl+C to stop")
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                pass

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass
