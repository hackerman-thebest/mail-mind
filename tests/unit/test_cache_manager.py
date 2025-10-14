"""
Unit Tests for CacheManager

Tests Story 1.6: Performance Optimization & Caching (AC1, AC8)
"""

import json
import pytest
import tempfile
import time
from pathlib import Path

from src.mailmind.core.cache_manager import CacheManager


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test_cache.db")
        yield db_path


@pytest.fixture
def cache_manager(temp_db):
    """Create CacheManager instance for testing."""
    return CacheManager(temp_db)


@pytest.fixture
def sample_analysis():
    """Sample analysis result for testing."""
    return {
        'priority': 'High',
        'confidence': 0.92,
        'summary': 'Important email about project deadline',
        'tags': ['deadline', 'project', 'urgent'],
        'sentiment': 'urgent',
        'action_items': ['Review proposal by Friday'],
        'processing_time_ms': 1847,
        'tokens_per_second': 52.3,
        'model_version': 'llama3.1:8b-instruct-q4_K_M'
    }


class TestCacheManagerInitialization:
    """Test CacheManager initialization."""

    def test_initialization(self, temp_db):
        """Test CacheManager initializes correctly."""
        manager = CacheManager(temp_db)
        assert manager.db_path == temp_db
        assert Path(temp_db).exists()

    def test_database_schema_creation(self, cache_manager):
        """Test database schema is created with correct tables and indexes."""
        import sqlite3
        conn = sqlite3.connect(cache_manager.db_path)
        cursor = conn.cursor()

        # Check table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='analysis_cache'")
        assert cursor.fetchone() is not None

        # Check indexes exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_cache_model_version'")
        assert cursor.fetchone() is not None

        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_cache_last_accessed'")
        assert cursor.fetchone() is not None

        conn.close()


class TestCachingOperations:
    """Test core caching operations."""

    def test_cache_miss(self, cache_manager):
        """Test cache miss returns None."""
        result = cache_manager.get_cached_analysis('nonexistent_id', 'llama3.1:8b-instruct-q4_K_M')
        assert result is None

    def test_cache_hit(self, cache_manager, sample_analysis):
        """Test cache hit returns cached analysis."""
        message_id = 'test_message_123'
        model_version = 'llama3.1:8b-instruct-q4_K_M'

        # Cache the analysis
        cache_manager.cache_analysis(message_id, sample_analysis, model_version)

        # Retrieve from cache
        cached = cache_manager.get_cached_analysis(message_id, model_version)

        assert cached is not None
        assert cached['priority'] == 'High'
        assert cached['confidence'] == 0.92
        assert cached['cache_hit'] is True
        assert 'cache_retrieval_time_ms' in cached

    def test_cache_retrieval_performance(self, cache_manager, sample_analysis):
        """Test cache retrieval completes in <100ms."""
        message_id = 'perf_test_message'
        model_version = 'llama3.1:8b-instruct-q4_K_M'

        # Cache the analysis
        cache_manager.cache_analysis(message_id, sample_analysis, model_version)

        # Retrieve and measure time
        start = time.time()
        cached = cache_manager.get_cached_analysis(message_id, model_version)
        retrieval_time_ms = (time.time() - start) * 1000

        assert cached is not None
        assert retrieval_time_ms < 100, f"Cache retrieval took {retrieval_time_ms:.2f}ms (expected <100ms)"

    def test_cache_stores_all_fields(self, cache_manager, sample_analysis):
        """Test cache stores all analysis fields correctly."""
        message_id = 'test_fields'
        model_version = 'llama3.1:8b-instruct-q4_K_M'

        cache_manager.cache_analysis(message_id, sample_analysis, model_version)
        cached = cache_manager.get_cached_analysis(message_id, model_version)

        assert cached['priority'] == sample_analysis['priority']
        assert cached['confidence'] == sample_analysis['confidence']
        assert cached['summary'] == sample_analysis['summary']
        assert cached['tags'] == sample_analysis['tags']
        assert cached['sentiment'] == sample_analysis['sentiment']
        assert cached['action_items'] == sample_analysis['action_items']
        assert cached['processing_time_ms'] == sample_analysis['processing_time_ms']


class TestCacheInvalidation:
    """Test cache invalidation strategies."""

    def test_invalidation_by_message_id(self, cache_manager, sample_analysis):
        """Test invalidating specific cache entry by message_id."""
        message_id = 'test_invalidate'
        model_version = 'llama3.1:8b-instruct-q4_K_M'

        # Cache and verify
        cache_manager.cache_analysis(message_id, sample_analysis, model_version)
        assert cache_manager.get_cached_analysis(message_id, model_version) is not None

        # Invalidate
        cache_manager.invalidate_entry(message_id)

        # Verify removal
        assert cache_manager.get_cached_analysis(message_id, model_version) is None

    def test_invalidation_by_model_version(self, cache_manager, sample_analysis):
        """Test invalidating all cache entries for a model version."""
        model_v1 = 'llama3.1:8b-instruct-q4_K_M'
        model_v2 = 'llama3.2:3b-instruct-q4_K_M'

        # Cache multiple analyses with different model versions
        cache_manager.cache_analysis('msg1', sample_analysis, model_v1)
        cache_manager.cache_analysis('msg2', sample_analysis, model_v1)
        cache_manager.cache_analysis('msg3', sample_analysis, model_v2)

        # Invalidate model_v1
        deleted_count = cache_manager.invalidate_by_model_version(model_v1)

        assert deleted_count == 2
        assert cache_manager.get_cached_analysis('msg1', model_v1) is None
        assert cache_manager.get_cached_analysis('msg2', model_v1) is None
        assert cache_manager.get_cached_analysis('msg3', model_v2) is not None

    def test_model_version_mismatch_invalidates(self, cache_manager, sample_analysis):
        """Test cache invalidated automatically when model version changes."""
        message_id = 'test_version_mismatch'
        cached_model = 'llama3.1:8b-instruct-q4_K_M'
        current_model = 'llama3.2:3b-instruct-q4_K_M'

        # Cache with one model
        cache_manager.cache_analysis(message_id, sample_analysis, cached_model)

        # Try to retrieve with different model
        result = cache_manager.get_cached_analysis(message_id, current_model)

        assert result is None

    def test_clear_all_cache(self, cache_manager, sample_analysis):
        """Test clearing entire cache."""
        model_version = 'llama3.1:8b-instruct-q4_K_M'

        # Cache multiple analyses
        for i in range(5):
            cache_manager.cache_analysis(f'msg{i}', sample_analysis, model_version)

        # Clear all
        deleted_count = cache_manager.clear_all()

        assert deleted_count == 5
        assert cache_manager.get_cached_analysis('msg0', model_version) is None
        assert cache_manager.get_cached_analysis('msg4', model_version) is None


class TestCacheStatistics:
    """Test cache statistics and management."""

    def test_cache_stats_empty(self, cache_manager):
        """Test cache statistics for empty cache."""
        stats = cache_manager.get_cache_stats()

        assert stats['total_entries'] == 0
        assert stats['total_size_mb'] == 0.0

    def test_cache_stats_with_entries(self, cache_manager, sample_analysis):
        """Test cache statistics with cached entries."""
        model_version = 'llama3.1:8b-instruct-q4_K_M'

        # Cache multiple analyses
        for i in range(10):
            cache_manager.cache_analysis(f'msg{i}', sample_analysis, model_version)

        stats = cache_manager.get_cache_stats()

        assert stats['total_entries'] == 10
        assert stats['total_size_mb'] > 0
        assert len(stats['by_model']) == 1
        assert stats['by_model'][0]['model_version'] == model_version
        assert stats['by_model'][0]['entries'] == 10

    def test_access_count_increments(self, cache_manager, sample_analysis):
        """Test access count increments on cache hits."""
        message_id = 'test_access_count'
        model_version = 'llama3.1:8b-instruct-q4_K_M'

        # Cache analysis
        cache_manager.cache_analysis(message_id, sample_analysis, model_version)

        # Access multiple times
        for i in range(5):
            cached = cache_manager.get_cached_analysis(message_id, model_version)
            assert cached is not None

        # Check stats show access count
        stats = cache_manager.get_cache_stats()
        assert stats['avg_access_count'] > 0


class TestLRUEviction:
    """Test LRU cache eviction."""

    def test_lru_eviction(self, cache_manager, sample_analysis):
        """Test LRU eviction removes least recently used entries."""
        model_version = 'llama3.1:8b-instruct-q4_K_M'

        # Cache 20 analyses
        for i in range(20):
            cache_manager.cache_analysis(f'msg{i}', sample_analysis, model_version)
            time.sleep(0.01)  # Small delay to ensure different timestamps

        # Access first 10 to update last_accessed
        for i in range(10):
            cache_manager.get_cached_analysis(f'msg{i}', model_version)

        # Evict to keep only 15 entries
        evicted_count = cache_manager.evict_lru(max_entries=15)

        assert evicted_count == 5

        # Verify stats
        stats = cache_manager.get_cache_stats()
        assert stats['total_entries'] == 15

    def test_lru_eviction_no_change(self, cache_manager, sample_analysis):
        """Test LRU eviction when under limit."""
        model_version = 'llama3.1:8b-instruct-q4_K_M'

        # Cache 5 analyses
        for i in range(5):
            cache_manager.cache_analysis(f'msg{i}', sample_analysis, model_version)

        # Try to evict with higher limit
        evicted_count = cache_manager.evict_lru(max_entries=10)

        assert evicted_count == 0

        # Verify all entries still present
        stats = cache_manager.get_cache_stats()
        assert stats['total_entries'] == 5


class TestCacheErrorHandling:
    """Test cache error handling."""

    def test_corrupted_json_handling(self, cache_manager):
        """Test graceful handling of corrupted JSON in cache."""
        import sqlite3

        # Insert corrupted JSON directly into database
        conn = sqlite3.connect(cache_manager.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO analysis_cache
            (message_id, analysis_json, model_version, processing_time_ms)
            VALUES (?, ?, ?, ?)
        ''', ('corrupted_msg', 'INVALID JSON{', 'llama3.1:8b-instruct-q4_K_M', 1000))

        conn.commit()
        conn.close()

        # Try to retrieve - should handle gracefully
        result = cache_manager.get_cached_analysis('corrupted_msg', 'llama3.1:8b-instruct-q4_K_M')

        # Should return None instead of crashing
        assert result is None
