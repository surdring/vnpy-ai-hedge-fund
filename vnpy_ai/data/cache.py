"""In-memory cache with TTL support."""

from __future__ import annotations

import time
import threading
from typing import Any


class Cache:
    """Thread-safe in-memory cache with per-key TTL.

    Usage:
        cache = Cache(default_ttl=300)
        cache.set("prices:AAPL", [...])
        data = cache.get("prices:AAPL")  # returns None if expired
    """

    def __init__(self, default_ttl: int = 300) -> None:
        """Initialize cache.

        Args:
            default_ttl: Default time-to-live in seconds (default 300s = 5min).
        """
        self._default_ttl = default_ttl
        self._data: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any:
        """Get a value from cache. Returns None if missing or expired."""
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            expiry, value = entry
            if time.time() > expiry:
                del self._data[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a value in cache with optional per-key TTL."""
        ttl = ttl if ttl is not None else self._default_ttl
        expiry = time.time() + ttl
        with self._lock:
            self._data[key] = (expiry, value)

    def delete(self, key: str) -> None:
        """Remove a key from cache."""
        with self._lock:
            self._data.pop(key, None)

    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._data.clear()

    def cleanup(self) -> None:
        """Remove all expired entries."""
        with self._lock:
            now = time.time()
            expired = [
                k for k, (expiry, _) in self._data.items()
                if now > expiry
            ]
            for k in expired:
                del self._data[k]

    def __len__(self) -> int:
        with self._lock:
            return len(self._data)

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None
