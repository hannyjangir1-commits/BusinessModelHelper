"""Thread-safe bounded rate limiting with PostgreSQL multi-instance synchronization."""

import random
import threading
import time
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from sqlalchemy import delete, select
from sqlalchemy.orm import Session


class SlidingWindowRateLimiter:
    """Thread-safe, bounded sliding-window rate limiter with PostgreSQL backing.
    
    Prevents unbounded memory growth via LRU key eviction and active TTL purging.
    Synchronizes across application instances via the PostgreSQL database.
    """

    def __init__(self, max_in_memory_keys: int = 5000) -> None:
        self._lock = threading.Lock()
        self._max_in_memory_keys = max_in_memory_keys
        # OrderedDict provides bounded LRU eviction
        self._requests: Dict[str, List[float]] = OrderedDict()

    def is_rate_limited(
        self,
        key: str,
        max_attempts: int,
        window_seconds: int,
        db: Optional[Session] = None,
    ) -> Tuple[bool, int]:
        """Check if key has exceeded max_attempts in window_seconds.

        If a database session is provided, enforces and synchronizes state
        across multiple application instances using PostgreSQL.
        Falls back to bounded thread-safe in-memory sliding window.
        Returns (is_limited, retry_after_seconds).
        """
        now = time.time()

        # Multi-instance database synchronization if DB session is supplied
        if db is not None:
            try:
                return self._db_is_rate_limited(db, key, max_attempts, window_seconds, now)
            except Exception:
                # If database encounters a transient error, fall back to in-memory
                pass

        # In-memory bounded rate limiter
        with self._lock:
            return self._memory_is_rate_limited(key, max_attempts, window_seconds, now)

    def _db_is_rate_limited(
        self,
        db: Session,
        key: str,
        max_attempts: int,
        window_seconds: int,
        now: float,
    ) -> Tuple[bool, int]:
        from app.models.security import RateLimitEntry

        # Opportunistic cleanup of expired keys (5% of requests) to prevent unbounded table growth
        if random.random() < 0.05:
            try:
                db.execute(delete(RateLimitEntry).where(RateLimitEntry.expires_at < now))
                db.commit()
            except Exception:
                db.rollback()

        entry = db.execute(
            select(RateLimitEntry).where(RateLimitEntry.key == key)
        ).scalar_one_or_none()

        now_utc = datetime.now(timezone.utc)
        if entry is None or now >= entry.expires_at:
            if entry is None:
                entry = RateLimitEntry(
                    key=key,
                    attempts=1,
                    window_start=now,
                    expires_at=now + window_seconds,
                    updated_at=now_utc,
                )
                db.add(entry)
            else:
                entry.attempts = 1
                entry.window_start = now
                entry.expires_at = now + window_seconds
                entry.updated_at = now_utc

            try:
                db.commit()
            except Exception:
                db.rollback()

            with self._lock:
                self._record_in_memory(key, now, window_seconds)
            return False, 0

        if entry.attempts >= max_attempts:
            retry_after = max(1, int(entry.expires_at - now))
            return True, retry_after

        entry.attempts += 1
        entry.updated_at = now_utc
        try:
            db.commit()
        except Exception:
            db.rollback()

        with self._lock:
            self._record_in_memory(key, now, window_seconds)
        return False, 0

    def _memory_is_rate_limited(
        self,
        key: str,
        max_attempts: int,
        window_seconds: int,
        now: float,
    ) -> Tuple[bool, int]:
        timestamps = self._requests.get(key, [])
        valid_timestamps = [t for t in timestamps if now - t < window_seconds]

        # Active prune when approaching capacity
        if len(self._requests) >= self._max_in_memory_keys // 2:
            self._prune_expired_in_memory(now, window_seconds)

        if len(valid_timestamps) >= max_attempts:
            oldest = valid_timestamps[0]
            retry_after = int(window_seconds - (now - oldest)) + 1
            self._requests[key] = valid_timestamps
            if isinstance(self._requests, OrderedDict):
                self._requests.move_to_end(key)
            return True, max(1, retry_after)

        # Enforce strict bounded cardinality by evicting oldest entry if full
        if key not in self._requests and len(self._requests) >= self._max_in_memory_keys:
            if isinstance(self._requests, OrderedDict):
                self._requests.popitem(last=False)
            else:
                first_key = next(iter(self._requests))
                self._requests.pop(first_key, None)

        valid_timestamps.append(now)
        self._requests[key] = valid_timestamps
        if isinstance(self._requests, OrderedDict):
            self._requests.move_to_end(key)
        return False, 0

    def _record_in_memory(self, key: str, now: float, window_seconds: int) -> None:
        timestamps = self._requests.get(key, [])
        valid = [t for t in timestamps if now - t < window_seconds]
        if key not in self._requests and len(self._requests) >= self._max_in_memory_keys:
            if isinstance(self._requests, OrderedDict):
                self._requests.popitem(last=False)
        valid.append(now)
        self._requests[key] = valid
        if isinstance(self._requests, OrderedDict):
            self._requests.move_to_end(key)

    def _prune_expired_in_memory(self, now: float, window_seconds: int) -> None:
        expired = [
            k for k, ts in list(self._requests.items())
            if not ts or (now - ts[-1] >= window_seconds)
        ]
        for k in expired:
            self._requests.pop(k, None)

    def reset(self, key: str, db: Optional[Session] = None) -> None:
        """Reset attempts for a key upon successful authentication."""
        with self._lock:
            self._requests.pop(key, None)

        if db is not None:
            try:
                from app.models.security import RateLimitEntry
                db.execute(delete(RateLimitEntry).where(RateLimitEntry.key == key))
                db.commit()
            except Exception:
                db.rollback()


# Global instances for login, registration, and AI generation rate limiting
login_rate_limiter = SlidingWindowRateLimiter()
registration_rate_limiter = SlidingWindowRateLimiter()
generation_rate_limiter = SlidingWindowRateLimiter()
