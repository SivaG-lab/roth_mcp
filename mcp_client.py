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


async def create_mcp_session():
    """Create and return an MCP client session connected to the server."""
    server_params = StdioServerParameters(
        command=MCP_SERVER_CMD,
        args=MCP_SERVER_ARGS.split(),
    )
    read, write = await stdio_client(server_params).__aenter__()
    session = ClientSession(read, write)
    await session.__aenter__()
    await session.initialize()
    return session


async def discover_tools(session: ClientSession) -> list[dict]:
    """Discover MCP tools and translate to OpenAI function calling format."""
    tools_result = await session.list_tools()
    return [mcp_tool_to_openai_function(tool) for tool in tools_result.tools]


class ResilientToolExecutor:
    """Wraps MCP tool calls with retry and subprocess restart on failure."""

    def __init__(self, session: ClientSession, max_retries: int = 2):
        self.session = session
        self.max_retries = max_retries

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Call an MCP tool with retry logic.

        Returns the tool result as a string. On failure, retries up to
        max_retries times. Raises the last exception if all retries fail.
        """
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                result = await self.session.call_tool(tool_name, arguments)
                # Extract text content from MCP result
                if hasattr(result, "content") and result.content:
                    for block in result.content:
                        if hasattr(block, "text"):
                            return block.text
                return json.dumps({"error": "No text content in response"})
            except (ConnectionError, BrokenPipeError, OSError) as e:
                last_error = e
                logger.warning(
                    "MCP tool call failed (attempt %d/%d): %s",
                    attempt + 1, self.max_retries + 1, e,
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(0.5)
            except Exception as e:
                last_error = e
                logger.error("Unexpected error calling MCP tool %s: %s", tool_name, e)
                break

        raise last_error or RuntimeError(f"Failed to call tool {tool_name}")
