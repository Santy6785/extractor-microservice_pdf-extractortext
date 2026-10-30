"""Thread-safe LRU cache for PDF extraction results.

Uses an OrderedDict protected by a threading.Lock.
Keys are sha256 hex digests of the PDF bytes, and values are ExtractResponse DTOs.
If extract_cache_size is 0, caching is disabled and nothing is stored.
"""

from __future__ import annotations

import threading
from collections import OrderedDict

from app.core.config import Settings
from app.dtos.extraction import ExtractResponse


class LRUCache:
    """Thread-safe LRU cache with configurable maximum capacity."""

    def __init__(self, max_size: int | None = None) -> None:
        self._explicit_max_size = max_size
        self._cache: OrderedDict[str, ExtractResponse] = OrderedDict()
        self._lock = threading.Lock()

    @property
    def max_size(self) -> int:
        if self._explicit_max_size is not None:
            return self._explicit_max_size
        return Settings().extract_cache_size

    @max_size.setter
    def max_size(self, size: int | None) -> None:
        with self._lock:
            self._explicit_max_size = size
            if size is not None and size <= 0:
                self._cache.clear()
            elif size is not None:
                while len(self._cache) > size:
                    self._cache.popitem(last=False)

    def get(self, key: str) -> ExtractResponse | None:
        """Retrieve an item by key, updating its LRU position."""
        with self._lock:
            if self.max_size <= 0:
                return None
            if key not in self._cache:
                return None
            self._cache.move_to_end(key)
            return self._cache[key]

    def put(self, key: str, value: ExtractResponse) -> None:
        """Store an item by key, evicting the oldest if at capacity."""
        with self._lock:
            if self.max_size <= 0:
                return
            if key in self._cache:
                self._cache.move_to_end(key)
                self._cache[key] = value
                return
            if len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
            self._cache[key] = value

    def clear(self) -> None:
        """Clear all entries from the cache."""
        with self._lock:
            self._cache.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._cache)

    def __contains__(self, key: str) -> bool:
        with self._lock:
            return key in self._cache


# Default module-level cache instance using application settings
default_cache = LRUCache()


def get(key: str) -> ExtractResponse | None:
    """Get value from default LRU cache by key."""
    return default_cache.get(key)


def put(key: str, value: ExtractResponse) -> None:
    """Put value into default LRU cache by key."""
    default_cache.put(key, value)


def clear() -> None:
    """Clear default LRU cache."""
    default_cache.clear()


__all__ = ["LRUCache", "default_cache", "get", "put", "clear"]
