"""Configuration module — loads .env and exports validated config constants."""

import json as _json
import logging
import os
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from uuid import uuid4

from dotenv import load_dotenv

load_dotenv()

# Correlation ID for structured logging (async-safe via contextvars)
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


def new_correlation_id() -> str:
    """Generate and set a new correlation ID for the current context."""
    cid = uuid4().hex[:12]
    correlation_id_var.set(cid)
    return cid


class JsonLogFormatter(logging.Formatter):
    """Structured JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        cid = correlation_id_var.get("")
        if cid:
            entry["correlation_id"] = cid
        # Include extra fields passed via logger.info(..., extra={...})
        for key in ("tool_name", "duration_ms", "status", "elapsed",
                     "conversion", "years", "sections"):
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        return _json.dumps(entry)


# Log format: "text" (default) or "json"
_LOG_FORMAT: str = os.getenv("LOG_FORMAT", "text").lower()

if _LOG_FORMAT == "json":
    _handler = logging.StreamHandler()
    _handler.setFormatter(JsonLogFormatter())
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "WARNING"),
        handlers=[_handler],
    )
else:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "WARNING"),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

LOG_FORMAT: str = _LOG_FORMAT

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

# MCP Transport
MCP_TRANSPORT: str = os.getenv("MCP_TRANSPORT", "stdio")
MCP_HOST: str = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT: int = _safe_int("MCP_PORT", 8080)

# Response mode: "full" (HTML + data) or "data_only" (data dict only)
_raw_response_mode = os.getenv("RESPONSE_MODE", "full").lower()
if _raw_response_mode not in ("full", "data_only"):
    logging.warning("Unrecognized RESPONSE_MODE=%r, defaulting to 'full'", _raw_response_mode)
    _raw_response_mode = "full"
RESPONSE_MODE: str = _raw_response_mode

# Rate limiting (requests per minute, 0 = disabled)
MCP_RATE_LIMIT: int = _safe_int("MCP_RATE_LIMIT", 0)

# Log format: "text" (default) or "json"
LOG_FORMAT: str = os.getenv("LOG_FORMAT", "text").lower()


class ConfigError(RuntimeError):
    """Raised when required configuration is missing."""


def validate_config() -> None:
    """Validate that required configuration values are present."""
    if not OPENAI_API_KEY:
        raise ConfigError(
            "OPENAI_API_KEY not set. "
            "Copy .env.example to .env and add your API key."
        )
