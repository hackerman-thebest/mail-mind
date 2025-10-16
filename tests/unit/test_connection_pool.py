"""
Unit tests for OllamaConnectionPool (Story 3.3 AC2)

Tests verify connection pooling functionality including:
- Pool initialization and size limits
- Thread-safe connection acquisition/release
- Context manager pattern
- Pool statistics and health checking
- Concurrent access handling
- Connection exhaustion and timeout behavior
"""

import pytest
import time
import threading
import queue
from unittest.mock import Mock, patch, MagicMock

# Mock ollama before importing
mock_ollama = MagicMock()
mock_client_class = Mock()
mock_ollama.Client = mock_client_class

import sys
sys.modules['ollama'] = mock_ollama

from mailmind.core.ollama_manager import OllamaConnectionPool, OLLAMA_AVAILABLE


class TestOllamaConnectionPoolInitialization:
    """Test suite for connection pool initialization."""

    def test_pool_creation_valid_size(self):
        """Test AC2: Pool can be created with valid size (2-5)."""
        valid_sizes = [2, 3, 4, 5]

        for size in valid_sizes:
            pool = OllamaConnectionPool(size=size)
            assert pool.size == size
            assert pool.active_count == 0
            assert not pool._initialized

    def test_pool_creation_default_size(self):
        """Test AC2: Pool uses default size of 3 when not specified."""
        pool = OllamaConnectionPool()
        assert pool.size == 3

    def test_pool_creation_invalid_size_too_small(self):
        """Test AC2, arch-3: Pool size must be at least 2."""
        invalid_sizes = [0, 1, -1]

        for size in invalid_sizes:
            with pytest.raises(ValueError, match="Pool size must be between 2 and 5"):
                OllamaConnectionPool(size=size)

    def test_pool_creation_invalid_size_too_large(self):
        """Test AC2, arch-3: Pool size must be at most 5."""
        invalid_sizes = [6, 10, 100]

        for size in invalid_sizes:
            with pytest.raises(ValueError, match="Pool size must be between 2 and 5"):
                OllamaConnectionPool(size=size)

    def test_pool_creation_invalid_type(self):
        """Test AC2: Pool size must be an integer."""
        invalid_types = ["3", 3.5, None, [3], {"size": 3}]

        for size in invalid_types:
            with pytest.raises(ValueError, match="Pool size must be between 2 and 5"):
                OllamaConnectionPool(size=size)

    @patch('mailmind.core.ollama_manager.ollama.Client')
    @patch('mailmind.core.ollama_manager.OLLAMA_AVAILABLE', True)
    def test_pool_initialize_creates_connections(self, mock_client_class):
        """Test AC2: Pool initialization creates correct number of connections."""
        pool_size = 3
        pool = OllamaConnectionPool(size=pool_size)

        # Mock Client constructor to return mock connections
        mock_connections = [Mock() for _ in range(pool_size)]
        mock_client_class.side_effect = mock_connections

        pool.initialize()

        assert pool._initialized
        assert pool.pool.qsize() == pool_size
        assert mock_client_class.call_count == pool_size

    @patch('mailmind.core.ollama_manager.OLLAMA_AVAILABLE', False)
    def test_pool_initialize_fails_without_ollama(self):
        """Test AC2: Pool initialization fails if Ollama not available."""
        pool = OllamaConnectionPool(size=2)

        with pytest.raises(RuntimeError, match="Ollama client not available"):
            pool.initialize()

    @patch('mailmind.core.ollama_manager.ollama.Client')
    @patch('mailmind.core.ollama_manager.OLLAMA_AVAILABLE', True)
    def test_pool_initialize_idempotent(self, mock_client_class):
        """Test AC2: Calling initialize() multiple times is safe."""
        pool = OllamaConnectionPool(size=2)

        mock_client_class.side_effect = [Mock(), Mock()]
        pool.initialize()

        first_call_count = mock_client_class.call_count

        # Second initialization should not create more connections
        pool.initialize()

        assert mock_client_class.call_count == first_call_count


class TestOllamaConnectionPoolAcquisition:
    """Test suite for connection acquisition and release."""

    @patch('mailmind.core.ollama_manager.ollama.Client')
    @patch('mailmind.core.ollama_manager.OLLAMA_AVAILABLE', True)
    def test_acquire_connection_success(self, mock_client_class):
        """Test AC2: Connection can be acquired from initialized pool."""
        pool = OllamaConnectionPool(size=2)

        mock_conn1 = Mock()
        mock_conn2 = Mock()
        mock_client_class.side_effect = [mock_conn1, mock_conn2]

        pool.initialize()

        # Acquire connection using context manager
        with pool.acquire() as conn:
            assert conn == mock_conn1
            assert pool.active_count == 1

        # After exit, connection should be released
        assert pool.active_count == 0

    @patch('mailmind.core.ollama_manager.OLLAMA_AVAILABLE', True)
    def test_acquire_connection_not_initialized(self):
        """Test AC2: Acquiring from uninitialized pool raises error."""
        pool = OllamaConnectionPool(size=2)

        with pytest.raises(RuntimeError, match="Connection pool not initialized"):
            with pool.acquire():
                pass

    @patch('mailmind.core.ollama_manager.ollama.Client')
    @patch('mailmind.core.ollama_manager.OLLAMA_AVAILABLE', True)
    def test_acquire_multiple_connections(self, mock_client_class):
        """Test AC2: Multiple connections can be acquired concurrently."""
        pool = OllamaConnectionPool(size=3)

        mock_connections = [Mock() for _ in range(3)]
        mock_client_class.side_effect = mock_connections

        pool.initialize()

        acquired = []

        # Acquire 2 connections
        ctx1 = pool.acquire()
        conn1 = ctx1.__enter__()
        acquired.append((ctx1, conn1))

        ctx2 = pool.acquire()
        conn2 = ctx2.__enter__()
        acquired.append((ctx2, conn2))

        # Should have 2 active connections
        assert pool.active_count == 2
        assert conn1 in mock_connections
        assert conn2 in mock_connections
        assert conn1 != conn2

        # Release connections
        for ctx, conn in acquired:
            ctx.__exit__(None, None, None)

        assert pool.active_count == 0

    @patch('mailmind.core.ollama_manager.ollama.Client')
    @patch('mailmind.core.ollama_manager.OLLAMA_AVAILABLE', True)
    def test_acquire_connection_timeout(self, mock_client_class):
        """Test AC2, arch-7: Acquisition times out when pool exhausted."""
        pool = OllamaConnectionPool(size=2)

        mock_connections = [Mock(), Mock()]
        mock_client_class.side_effect = mock_connections

        pool.initialize()

        # Acquire all connections
        ctx1 = pool.acquire()
        conn1 = ctx1.__enter__()

        ctx2 = pool.acquire()
        conn2 = ctx2.__enter__()

        # Pool is now exhausted - try to acquire with short timeout
        with pytest.raises(queue.Empty):
            with pool.acquire(timeout=0.1):
                pass

        # Release connections
        ctx1.__exit__(None, None, None)
        ctx2.__exit__(None, None, None)

    @patch('mailmind.core.ollama_manager.ollama.Client')
    @patch('mailmind.core.ollama_manager.OLLAMA_AVAILABLE', True)
    def test_acquire_connection_released_on_exception(self, mock_client_class):
        """Test AC2, arch-8: Connection released even when exception occurs."""
        pool = OllamaConnectionPool(size=2)

        mock_conn = Mock()
        mock_client_class.side_effect = [mock_conn, Mock()]

        pool.initialize()

        # Raise exception inside context manager
        try:
            with pool.acquire() as conn:
                assert pool.active_count == 1
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Connection should still be released
        assert pool.active_count == 0

        # Pool should still be usable
        with pool.acquire() as conn:
            assert conn is not None


class TestOllamaConnectionPoolStatistics:
    """Test suite for pool statistics and monitoring."""

    @patch('mailmind.core.ollama_manager.ollama.Client')
    @patch('mailmind.core.ollama_manager.OLLAMA_AVAILABLE', True)
    def test_pool_stats_initial(self, mock_client_class):
        """Test AC2: Pool statistics correct after initialization."""
        pool = OllamaConnectionPool(size=3)

        mock_client_class.side_effect = [Mock(), Mock(), Mock()]
        pool.initialize()

        stats = pool.stats()

        assert stats['total'] == 3
        assert stats['active'] == 0
        assert stats['idle'] == 3

    @patch('mailmind.core.ollama_manager.ollama.Client')
    @patch('mailmind.core.ollama_manager.OLLAMA_AVAILABLE', True)
    def test_pool_stats_with_active_connections(self, mock_client_class):
        """Test AC2: Pool statistics update correctly with active connections."""
        pool = OllamaConnectionPool(size=3)

        mock_client_class.side_effect = [Mock(), Mock(), Mock()]
        pool.initialize()

        # Acquire 2 connections
        ctx1 = pool.acquire()
        conn1 = ctx1.__enter__()

        ctx2 = pool.acquire()
        conn2 = ctx2.__enter__()

        stats = pool.stats()

        assert stats['total'] == 3
        assert stats['active'] == 2
        assert stats['idle'] == 1

        # Release connections
        ctx1.__exit__(None, None, None)
        ctx2.__exit__(None, None, None)

        stats = pool.stats()
        assert stats['active'] == 0
        assert stats['idle'] == 3

    @patch('mailmind.core.ollama_manager.ollama.Client')
    @patch('mailmind.core.ollama_manager.OLLAMA_AVAILABLE', True)
    def test_pool_health_check_healthy(self, mock_client_class):
        """Test AC2: Health check returns True for healthy pool."""
        pool = OllamaConnectionPool(size=2)

        mock_client_class.side_effect = [Mock(), Mock()]
        pool.initialize()

        assert pool.health_check() is True

    def test_pool_health_check_not_initialized(self):
        """Test AC2: Health check returns False for uninitialized pool."""
        pool = OllamaConnectionPool(size=2)

        assert pool.health_check() is False


class TestOllamaConnectionPoolConcurrency:
    """Test suite for concurrent access to connection pool."""

    @patch('mailmind.core.ollama_manager.ollama.Client')
    @patch('mailmind.core.ollama_manager.OLLAMA_AVAILABLE', True)
    def test_pool_concurrent_acquisition(self, mock_client_class):
        """Test AC2, arch-2: Pool handles concurrent access safely."""
        pool = OllamaConnectionPool(size=3)

        mock_client_class.side_effect = [Mock() for _ in range(3)]
        pool.initialize()

        results = []
        errors = []

        def worker(worker_id):
            try:
                with pool.acquire(timeout=2.0) as conn:
                    # Simulate work
                    time.sleep(0.01)
                    results.append((worker_id, conn))
            except Exception as e:
                errors.append((worker_id, e))

        # Create 10 threads competing for 3 connections
        threads = []
        for i in range(10):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join(timeout=5.0)

        # All threads should succeed (queuing should work)
        assert len(results) == 10
        assert len(errors) == 0

        # All connections should be released
        assert pool.active_count == 0

    @patch('mailmind.core.ollama_manager.ollama.Client')
    @patch('mailmind.core.ollama_manager.OLLAMA_AVAILABLE', True)
    def test_pool_no_deadlock(self, mock_client_class):
        """Test AC2, arch-2: No deadlocks with concurrent access."""
        pool = OllamaConnectionPool(size=2)

        mock_client_class.side_effect = [Mock(), Mock()]
        pool.initialize()

        def worker():
            for _ in range(5):
                with pool.acquire(timeout=1.0) as conn:
                    time.sleep(0.001)

        threads = [threading.Thread(target=worker) for _ in range(5)]

        for t in threads:
            t.start()

        for t in threads:
            t.join(timeout=10.0)
            assert not t.is_alive(), "Thread deadlocked"

    @patch('mailmind.core.ollama_manager.ollama.Client')
    @patch('mailmind.core.ollama_manager.OLLAMA_AVAILABLE', True)
    def test_pool_thread_safe_stats(self, mock_client_class):
        """Test AC2, arch-2: Statistics are thread-safe."""
        pool = OllamaConnectionPool(size=3)

        mock_client_class.side_effect = [Mock() for _ in range(3)]
        pool.initialize()

        stats_results = []

        def stats_reader():
            for _ in range(20):
                stats = pool.stats()
                stats_results.append(stats)
                time.sleep(0.001)

        def conn_user():
            for _ in range(10):
                with pool.acquire(timeout=1.0):
                    time.sleep(0.002)

        # Run stats reader and connection users concurrently
        threads = [
            threading.Thread(target=stats_reader),
            threading.Thread(target=conn_user),
            threading.Thread(target=conn_user),
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join(timeout=10.0)

        # All stat calls should succeed and be consistent
        for stats in stats_results:
            assert stats['total'] == 3
            assert 0 <= stats['active'] <= 3
            assert stats['active'] + stats['idle'] == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
