"""MCP client session management with ResilientToolExecutor."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from config import MCP_SERVER_CMD, MCP_SERVER_ARGS
from schema_converter import mcp_tool_to_openai_function

logger = logging.getLogger(__name__)


class MCPConnection:
    """Manages MCP session lifecycle, storing context manager references for proper cleanup."""

    def __init__(self):
        self.session: ClientSession | None = None
        self._stdio_cm = None
        self._session_cm = None

    async def connect(self) -> ClientSession:
        """Create and return an MCP client session connected to the server."""
        server_params = StdioServerParameters(
            command=MCP_SERVER_CMD,
            args=MCP_SERVER_ARGS.split(),
        )
        self._stdio_cm = stdio_client(server_params)
        read, write = await self._stdio_cm.__aenter__()
        self._session_cm = ClientSession(read, write)
        self.session = await self._session_cm.__aenter__()
        await self.session.initialize()
        return self.session

    async def close(self):
        """Cleanly close the session and stdio transport."""
        if self._session_cm is not None:
            try:
                await self._session_cm.__aexit__(None, None, None)
            except Exception:
                logger.debug("Error closing MCP session", exc_info=True)
            self._session_cm = None
        if self._stdio_cm is not None:
            try:
                await self._stdio_cm.__aexit__(None, None, None)
            except Exception:
                logger.debug("Error closing stdio transport", exc_info=True)
            self._stdio_cm = None
        self.session = None

    async def __aenter__(self) -> ClientSession:
        return await self.connect()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


async def create_mcp_session():
    """Create and return an MCP client session connected to the server.

    DEPRECATED: Use MCPConnection for proper lifecycle management.
    This function leaks context managers — kept for backward compatibility.
    """
    conn = MCPConnection()
    return await conn.connect(), conn


async def discover_tools(session: ClientSession) -> list[dict]:
    """Discover MCP tools and translate to OpenAI function calling format."""
    tools_result = await session.list_tools()
    return [mcp_tool_to_openai_function(tool) for tool in tools_result.tools]


class ResilientToolExecutor:
    """Wraps MCP tool calls with retry and subprocess restart on failure."""

    def __init__(self, session: ClientSession, max_retries: int = 2,
                 session_factory=None):
        self.session = session
        self.max_retries = max_retries
        self._session_factory = session_factory
        self._lock = asyncio.Lock()

    async def _reconnect(self):
        """Attempt to create a new session via the factory."""
        if self._session_factory is None:
            return False
        try:
            self.session = await self._session_factory()
            logger.info("Reconnected MCP session via factory")
            return True
        except Exception:
            logger.error("Failed to reconnect MCP session", exc_info=True)
            return False

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Call an MCP tool with retry logic.

        Returns the tool result as a string. On failure, retries up to
        max_retries times. Raises the last exception if all retries fail.
        """
        last_error = None
        async with self._lock:
            for attempt in range(self.max_retries + 1):
                try:
                    result = await self.session.call_tool(tool_name, arguments)
                    # Extract text content from MCP result
                    if hasattr(result, "content") and result.content:
                        for block in result.content:
                            if hasattr(block, "text"):
                                return block.text
                    return json.dumps({"error": "No text content in response"})
                except (ConnectionError, BrokenPipeError, OSError, TimeoutError,
                        asyncio.TimeoutError) as e:
                    last_error = e
                    logger.warning(
                        "MCP tool call failed (attempt %d/%d): %s",
                        attempt + 1, self.max_retries + 1, e,
                    )
                    if attempt < self.max_retries:
                        await self._reconnect()
                        await asyncio.sleep(0.5)
                except Exception as e:
                    last_error = e
                    logger.error("Unexpected error calling MCP tool %s: %s", tool_name, e)
                    break

        raise last_error or RuntimeError(f"Failed to call tool {tool_name}")
