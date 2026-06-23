"""
Per-user sliding-window rate limiter.

Counts requests in the last *window_seconds* using monotonic timestamps.
When a user already has *max_calls* timestamps in that window, the next
request is rejected (call is not recorded).

Note: in-process storage is correct for a single worker. With multiple
Gunicorn/uWSGI workers, use Redis (or similar) so all workers share state.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from typing import DefaultDict, Deque


class SlidingWindowRateLimiter:
    def __init__(self, max_calls: int, window_seconds: float) -> None:
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self._events: DefaultDict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def is_allowed(self, key: str) -> bool:
        """Return True if the request may proceed; False if rate limited."""
        now = time.monotonic()
        cutoff = now - self.window_seconds

        with self._lock:
            timestamps = self._events[key]
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()

            if len(timestamps) >= self.max_calls:
                return False

            timestamps.append(now)
            return True

    def reset(self) -> None:
        """Clear all counters (useful in tests)."""
        with self._lock:
            self._events.clear()
