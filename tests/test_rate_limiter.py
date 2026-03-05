"""T042 — Rate limiter tests."""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from rate_limiter import RateLimiter


class TestRateLimiter:
    def test_disabled_when_zero(self):
        rl = RateLimiter(0)
        assert not rl.enabled
        assert rl.check() is True

    def test_allows_under_limit(self):
        rl = RateLimiter(5)
        for _ in range(5):
            assert rl.check() is True

    def test_blocks_over_limit(self):
        rl = RateLimiter(3)
        for _ in range(3):
            assert rl.check() is True
        assert rl.check() is False

    def test_sliding_window_expires(self):
        rl = RateLimiter(2)
        assert rl.check() is True
        assert rl.check() is True
        assert rl.check() is False
        # Simulate time passing by manipulating the deque
        rl._window[0] = time.monotonic() - 61
        rl._window[1] = time.monotonic() - 61
        assert rl.check() is True

    def test_enabled_property(self):
        assert RateLimiter(0).enabled is False
        assert RateLimiter(1).enabled is True
        assert RateLimiter(100).enabled is True
