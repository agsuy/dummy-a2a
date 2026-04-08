"""Shared pytest fixtures."""

from dummy_a2a.testing import (
    a2a_http,
    a2a_https_http,
    a2a_https_server,
    a2a_https_url,
    a2a_server,
    a2a_url,
    webhook_receiver,
)

__all__ = [
    "a2a_server",
    "a2a_url",
    "a2a_http",
    "a2a_https_server",
    "a2a_https_url",
    "a2a_https_http",
    "webhook_receiver",
]
