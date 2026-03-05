"""In-memory sliding window rate limiter for MCP tool calls."""

from __future__ import annotations

import time
from collections import deque


class RateLimiter:
    """Global sliding-window rate limiter (requests per minute)."""

    def __init__(self, max_requests_per_minute: int = 0):
        self.max_rpm = max_requests_per_minute
        self._window: deque[float] = deque()

    @property
    def enabled(self) -> bool:
        return self.max_rpm > 0

    def check(self) -> bool:
        """Return True if the request is allowed, False if rate-limited."""
        if not self.enabled:
            return True
        now = time.monotonic()
        # Remove entries older than 60 seconds
        while self._window and self._window[0] <= now - 60:
            self._window.popleft()
        if len(self._window) >= self.max_rpm:
            return False
        self._window.append(now)
        return True
