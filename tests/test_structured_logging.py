"""T038 — Structured logging tests."""

from __future__ import annotations

import json
import logging

import pytest

from config import JsonLogFormatter, correlation_id_var, new_correlation_id


class TestJsonLogFormatter:
    def test_produces_valid_json(self):
        formatter = JsonLogFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="Test message", args=(), exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"
        assert "timestamp" in parsed

    def test_includes_correlation_id(self):
        formatter = JsonLogFormatter()
        cid = new_correlation_id()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="With CID", args=(), exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["correlation_id"] == cid

    def test_includes_extra_fields(self):
        formatter = JsonLogFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="Extra", args=(), exc_info=None,
        )
        record.tool_name = "test_tool"
        record.duration_ms = 42.5
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["tool_name"] == "test_tool"
        assert parsed["duration_ms"] == 42.5


class TestCorrelationId:
    def test_new_correlation_id(self):
        cid = new_correlation_id()
        assert len(cid) == 12
        assert correlation_id_var.get() == cid

    def test_unique_ids(self):
        ids = {new_correlation_id() for _ in range(100)}
        assert len(ids) == 100
