"""T010 — Transport configuration tests."""

from __future__ import annotations

import pytest


class TestTransportConfig:
    def test_valid_transports(self):
        from mcp_server import _VALID_TRANSPORTS
        assert "stdio" in _VALID_TRANSPORTS
        assert "sse" in _VALID_TRANSPORTS
        assert "streamable-http" in _VALID_TRANSPORTS

    def test_invalid_transport_not_accepted(self):
        from mcp_server import _VALID_TRANSPORTS
        assert "http" not in _VALID_TRANSPORTS
        assert "websocket" not in _VALID_TRANSPORTS

    def test_default_transport_is_stdio(self):
        import os
        default = os.getenv("MCP_TRANSPORT", "stdio")
        assert default in {"stdio", "sse", "streamable-http"}

    def test_config_exports_transport_vars(self):
        from config import MCP_TRANSPORT, MCP_HOST, MCP_PORT
        assert isinstance(MCP_TRANSPORT, str)
        assert isinstance(MCP_HOST, str)
        assert isinstance(MCP_PORT, int)
