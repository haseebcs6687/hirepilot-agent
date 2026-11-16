"""Rate limiter implementation for free tier LLM APIs."""

from __future__ import annotations

import asyncio
import threading
import time
from collections import deque


class SlidingWindowRateLimiter:
    """Sliding-window rate limiter tracking requests within a time window (e.g. 60s)."""

    def __init__(self, max_requests: int, window_seconds: float = 60.0) -> None:
        if max_requests <= 0:
            raise ValueError("max_requests must be greater than 0")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._timestamps: deque[float] = deque()
        self._lock = threading.Lock()
        self._async_lock = asyncio.Lock()

    def _prune(self, now: float) -> None:
        threshold = now - self.window_seconds
        while self._timestamps and self._timestamps[0] <= threshold:
            self._timestamps.popleft()

    def can_acquire(self) -> bool:
        """Check if a slot is currently available without consuming it."""
        now = time.time()
        with self._lock:
            self._prune(now)
            return len(self._timestamps) < self.max_requests

    def acquire_sync(self, timeout: float = 30.0) -> bool:
        """Synchronously wait until a request slot is available, then record it."""
        start_time = time.time()
        while True:
            now = time.time()
            with self._lock:
                self._prune(now)
                if len(self._timestamps) < self.max_requests:
                    self._timestamps.append(now)
                    return True

                oldest = self._timestamps[0]
                sleep_needed = (oldest + self.window_seconds) - now

            if (time.time() - start_time) + sleep_needed > timeout:
                return False

            if sleep_needed > 0:
                time.sleep(min(sleep_needed + 0.05, timeout))

    async def acquire_async(self, timeout: float = 30.0) -> bool:
        """Asynchronously wait until a request slot is available, then record it."""
        start_time = time.time()
        while True:
            now = time.time()
            async with self._async_lock:
                with self._lock:
                    self._prune(now)
                    if len(self._timestamps) < self.max_requests:
                        self._timestamps.append(now)
                        return True

                    oldest = self._timestamps[0]
                    sleep_needed = (oldest + self.window_seconds) - now

            if (time.time() - start_time) + sleep_needed > timeout:
                return False

            if sleep_needed > 0:
                await asyncio.sleep(min(sleep_needed + 0.05, timeout))
