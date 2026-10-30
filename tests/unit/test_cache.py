"""Unit tests for the thread-safe LRU cache and cached extraction - Task 6a."""

import hashlib
import os
import pytest

from app.dtos.extraction import ExtractResponse
from app.services import cache
from app.services.cache import LRUCache
from app.services.extraction import extract_pdf_text

pdf_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "stress", "pdfs"))
real_pdf_path = os.path.join(pdf_dir, "2020-Scrum-Guide-Spanish-Latin-South-American.pdf")


def test_cache_hit_returns_same_result_real_pdf():
    """Verify that a cache hit returns the exact same result for a real PDF."""
    if not os.path.isfile(real_pdf_path):
        pytest.skip("Real PDF not found for testing")

    cache.clear()
    with open(real_pdf_path, "rb") as f:
        pdf_bytes = f.read()

    key = hashlib.sha256(pdf_bytes).hexdigest()
    assert cache.get(key) is None

    # First extraction: cache miss -> extracted and stored
    result1 = extract_pdf_text(pdf_bytes)
    assert result1 is not None
    assert result1.page_count == 16
    assert isinstance(result1.content, str) and len(result1.content) > 0

    # Key is now in cache
    cached_entry = cache.get(key)
    assert cached_entry is not None
    assert cached_entry.content == result1.content

    # Second extraction: cache hit -> returned from cache
    result2 = extract_pdf_text(pdf_bytes)
    assert result1 == result2
    assert result1.content == result2.content
    assert result1.page_count == result2.page_count
    # Should be the identical object from cache
    assert result2 is cached_entry


def test_cache_size_zero_does_not_store():
    """Verify that if cache size is 0, nothing is stored in the cache."""
    c = LRUCache(max_size=0)
    dummy_resp = ExtractResponse(content="# Test", page_count=1)

    c.put("dummy_key", dummy_resp)
    assert c.get("dummy_key") is None
    assert len(c) == 0

    # Test via default cache with size 0
    orig_max_size = cache.default_cache._explicit_max_size
    try:
        cache.default_cache.max_size = 0
        cache.clear()

        pdf_bytes = b"%PDF-1.4 minimal dummy bytes"
        key = hashlib.sha256(pdf_bytes).hexdigest()
        cache.put(key, dummy_resp)
        assert cache.get(key) is None
        assert len(cache.default_cache) == 0
    finally:
        cache.default_cache.max_size = orig_max_size
        cache.clear()


def test_lru_discards_oldest():
    """Verify that LRUCache evicts the least recently used item."""
    c = LRUCache(max_size=2)
    resp1 = ExtractResponse(content="Page 1", page_count=1)
    resp2 = ExtractResponse(content="Page 2", page_count=2)
    resp3 = ExtractResponse(content="Page 3", page_count=3)

    # 1. Without access: oldest item inserted is evicted
    c.put("k1", resp1)
    c.put("k2", resp2)
    assert len(c) == 2
    assert c.get("k1") == resp1
    assert c.get("k2") == resp2

    # Adding third item should evict k1 (since k2 was accessed most recently above)
    c.put("k3", resp3)
    assert c.get("k1") is None, "k1 should have been evicted as LRU"
    assert c.get("k2") == resp2
    assert c.get("k3") == resp3

    # 2. With access: accessing k2 makes k3 the oldest
    c.clear()
    c.put("k1", resp1)
    c.put("k2", resp2)
    # Access k1 to make it most recently used; k2 is now the oldest
    _ = c.get("k1")
    c.put("k4", resp3)
    assert c.get("k2") is None, "k2 should have been evicted as LRU"
    assert c.get("k1") == resp1
    assert c.get("k4") == resp3
