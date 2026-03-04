"""Configuration module — loads .env and exports validated config constants."""

import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

# Logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "WARNING"),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

def _safe_int(env_var: str, default: int) -> int:
    try:
        return int(os.getenv(env_var, str(default)))
    except (ValueError, TypeError):
        return default


def _safe_float(env_var: str, default: float) -> float:
    try:
        return float(os.getenv(env_var, str(default)))
    except (ValueError, TypeError):
        return default


# OpenAI
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TIMEOUT: int = _safe_int("OPENAI_TIMEOUT", 30)

# Cost control
MAX_SESSION_COST: float = _safe_float("MAX_SESSION_COST", 0.50)

# MCP Server
MCP_SERVER_CMD: str = os.getenv("MCP_SERVER_CMD", "python")
MCP_SERVER_ARGS: str = os.getenv("MCP_SERVER_ARGS", "mcp_server.py")


class ConfigError(RuntimeError):
    """Raised when required configuration is missing."""


def validate_config() -> None:
    """Validate that required configuration values are present."""
    if not OPENAI_API_KEY:
        raise ConfigError(
            "OPENAI_API_KEY not set. "
            "Copy .env.example to .env and add your API key."
        )
