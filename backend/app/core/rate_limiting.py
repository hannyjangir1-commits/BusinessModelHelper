"""Thread-safe in-memory rate limiting with sliding window."""

import threading
import time
from typing import Dict, List, Tuple


class SlidingWindowRateLimiter:
    """Sliding-window rate limiter for sensitive authentication endpoints."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._requests: Dict[str, List[float]] = {}

    def is_rate_limited(self, key: str, max_attempts: int, window_seconds: int) -> Tuple[bool, int]:
        """Check if key has exceeded max_attempts in window_seconds.

        Returns (is_limited, retry_after_seconds).
        """
        now = time.time()
        with self._lock:
            # Clean expired timestamps
            timestamps = self._requests.get(key, [])
            valid_timestamps = [t for t in timestamps if now - t < window_seconds]

            if len(valid_timestamps) >= max_attempts:
                oldest = valid_timestamps[0]
                retry_after = int(window_seconds - (now - oldest)) + 1
                self._requests[key] = valid_timestamps
                return True, max(1, retry_after)

            # Record this attempt
            valid_timestamps.append(now)
            self._requests[key] = valid_timestamps
            return False, 0

    def reset(self, key: str) -> None:
        """Reset attempts for a key upon successful authentication."""
        with self._lock:
            self._requests.pop(key, None)


# Global instances for login, registration, and AI generation rate limiting
login_rate_limiter = SlidingWindowRateLimiter()
registration_rate_limiter = SlidingWindowRateLimiter()
generation_rate_limiter = SlidingWindowRateLimiter()
