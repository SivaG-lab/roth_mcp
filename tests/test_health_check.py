"""T032 — Health check tool tests."""

from __future__ import annotations

import json
import time

import pytest

from mcp_server import health_check, SERVER_VERSION


class TestHealthCheck:
    def test_returns_healthy_status(self):
        result = json.loads(health_check())
        data = result.get("data", result)
        assert data["status"] == "healthy"

    def test_returns_version(self):
        result = json.loads(health_check())
        data = result.get("data", result)
        assert data["version"] == SERVER_VERSION

    def test_returns_tool_count(self):
        result = json.loads(health_check())
        data = result.get("data", result)
        assert data["tools_available"] == 7

    def test_returns_uptime(self):
        result = json.loads(health_check())
        data = result.get("data", result)
        assert isinstance(data["uptime_seconds"], (int, float))
        assert data["uptime_seconds"] >= 0

    def test_responds_fast(self):
        start = time.monotonic()
        health_check()
        elapsed_ms = (time.monotonic() - start) * 1000
        assert elapsed_ms < 100, f"Health check took {elapsed_ms:.1f}ms (limit: 100ms)"
