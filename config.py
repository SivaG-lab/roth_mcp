"""Configuration module — loads .env and exports validated config constants."""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

# OpenAI
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TIMEOUT: int = int(os.getenv("OPENAI_TIMEOUT", "30"))

# Cost control
MAX_SESSION_COST: float = float(os.getenv("MAX_SESSION_COST", "0.50"))

# MCP Server
MCP_SERVER_CMD: str = os.getenv("MCP_SERVER_CMD", "python")
MCP_SERVER_ARGS: str = os.getenv("MCP_SERVER_ARGS", "mcp_server.py")


def validate_config() -> None:
    """Validate that required configuration values are present."""
    if not OPENAI_API_KEY:
        print(
            "ERROR: OPENAI_API_KEY not set. "
            "Copy .env.example to .env and add your API key.",
            file=sys.stderr,
        )
        sys.exit(1)
