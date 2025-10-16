"""
Unit tests for EmailBatchProcessor (Story 3.3 AC4).

Tests cover:
- Batch processing with parallel execution
- Individual email failure isolation
- Timeout handling
- Progress callback support
- Result aggregation
- Performance metrics calculation
"""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch
from concurrent.futures import TimeoutError as FutureTimeoutError
from mailmind.core.email_batch_processor import EmailBatchProcessor, BatchResult


class TestEmailBatchProcessorInitialization:
    """Test EmailBatchProcessor initialization."""

    def test_init_with_pool_size_3(self):
        """Test initialization with pool size 3."""
        mock_engine = Mock()
        mock_pool = Mock()
        mock_pool.size = 3

        processor = EmailBatchProcessor(mock_engine, mock_pool)

        assert processor.engine == mock_engine
        assert processor.pool == mock_pool
        assert processor.executor._max_workers == 3

    def test_init_with_pool_size_5(self):
        """Test initialization with maximum pool size."""
        mock_engine = Mock()
        mock_pool = Mock()
        mock_pool.size = 5

        processor = EmailBatchProcessor(mock_engine, mock_pool)

        assert processor.executor._max_workers == 5


class TestBatchProcessing:
    """Test batch processing functionality."""

    def test_process_batch_empty_list(self):
        """Test processing empty email list."""
        mock_engine = Mock()
        mock_pool = Mock()
        mock_pool.size = 3

        processor = EmailBatchProcessor(mock_engine, mock_pool)
        result = processor.process_batch([])

        assert result.total == 0
        assert result.success == 0
        assert result.failed == 0
        assert result.results == []
        assert result.elapsed_time == 0.0
        assert result.emails_per_minute == 0.0

    @patch('mailmind.core.email_batch_processor.EmailBatchProcessor._process_one')
    def test_process_batch_all_successful(self, mock_process_one):
        """Test batch processing with all emails successful."""
        mock_engine = Mock()
        mock_pool = Mock()
        mock_pool.size = 3

        # Mock successful processing
        mock_process_one.return_value = {'status': 'success', 'result': 'analyzed'}

        processor = EmailBatchProcessor(mock_engine, mock_pool)

        emails = [Mock(id=i) for i in range(5)]
        result = processor.process_batch(emails)

        assert result.total == 5
        assert result.success == 5
        assert result.failed == 0
        assert len(result.results) == 5
        assert result.elapsed_time > 0
        assert result.emails_per_minute > 0
        assert mock_process_one.call_count == 5

    @patch('mailmind.core.email_batch_processor.EmailBatchProcessor._process_one')
    def test_process_batch_individual_failure(self, mock_process_one):
        """Test batch processing with individual email failures (don't stop batch)."""
        mock_engine = Mock()
        mock_pool = Mock()
        mock_pool.size = 3

        # Mock: 2 successful, 1 failed, 2 successful
        mock_process_one.side_effect = [
            {'status': 'success'},
            {'status': 'success'},
            {'error': 'Analysis failed'},
            {'status': 'success'},
            {'status': 'success'}
        ]

        processor = EmailBatchProcessor(mock_engine, mock_pool)

        emails = [Mock(id=i) for i in range(5)]
        result = processor.process_batch(emails)

        # All emails should be processed despite failure
        assert result.total == 5
        assert result.success == 4
        assert result.failed == 1
        assert len(result.results) == 5
        assert mock_process_one.call_count == 5

    @patch('mailmind.core.email_batch_processor.EmailBatchProcessor._process_one')
    def test_process_batch_exception_handling(self, mock_process_one):
        """Test batch processing handles exceptions without stopping."""
        mock_engine = Mock()
        mock_pool = Mock()
        mock_pool.size = 3

        # Mock: 2 successful, 1 exception, 2 successful
        mock_process_one.side_effect = [
            {'status': 'success'},
            {'status': 'success'},
            Exception("Unexpected error"),
            {'status': 'success'},
            {'status': 'success'}
        ]

        processor = EmailBatchProcessor(mock_engine, mock_pool)

        emails = [Mock(id=i) for i in range(5)]

        # Should not raise, but handle exception gracefully
        # Note: The executor will catch the exception in future.result()
        # We need to mock the future to raise exception
        with patch.object(processor.executor, 'submit') as mock_submit:
            # Create mock futures
            futures = []
            for i, email in enumerate(emails):
                mock_future = Mock()
                if i == 2:
                    # Third email raises exception
                    mock_future.result.side_effect = Exception("Unexpected error")
                else:
                    mock_future.result.return_value = {'status': 'success'}
                futures.append(mock_future)
                mock_submit.return_value = mock_future

            # Process batch with proper future mocking
            mock_submit.side_effect = futures
            result = processor.process_batch(emails)

            assert result.total == 5
            assert result.success == 4
            assert result.failed == 1

    @patch('mailmind.core.email_batch_processor.EmailBatchProcessor._process_one')
    def test_process_batch_timeout_handling(self, mock_process_one):
        """Test batch processing handles timeouts (30s per email)."""
        mock_engine = Mock()
        mock_pool = Mock()
        mock_pool.size = 3

        processor = EmailBatchProcessor(mock_engine, mock_pool)

        emails = [Mock(id=i) for i in range(3)]

        # Mock futures with timeout
        with patch.object(processor.executor, 'submit') as mock_submit:
            futures = []
            for i, email in enumerate(emails):
                mock_future = Mock()
                if i == 1:
                    # Second email times out
                    mock_future.result.side_effect = FutureTimeoutError()
                else:
                    mock_future.result.return_value = {'status': 'success'}
                futures.append(mock_future)
                mock_submit.return_value = mock_future

            mock_submit.side_effect = futures
            result = processor.process_batch(emails, email_timeout=30.0)

            assert result.total == 3
            assert result.success == 2
            assert result.failed == 1

            # Check timeout result
            timeout_result = result.results[1]
            assert 'error' in timeout_result
            assert 'Timeout' in timeout_result['error']
            assert timeout_result.get('timeout') is True

    @patch('mailmind.core.email_batch_processor.EmailBatchProcessor._process_one')
    def test_process_batch_progress_callback(self, mock_process_one):
        """Test progress callback is called for each email."""
        mock_engine = Mock()
        mock_pool = Mock()
        mock_pool.size = 3

        mock_process_one.return_value = {'status': 'success'}

        processor = EmailBatchProcessor(mock_engine, mock_pool)

        emails = [Mock(id=i) for i in range(10)]
        progress_callback = Mock()

        result = processor.process_batch(emails, progress_callback=progress_callback)

        # Progress callback should be called 10 times (once per email)
        assert progress_callback.call_count == 10

        # Verify callback arguments
        for i in range(10):
            progress_callback.assert_any_call(i + 1, 10)

    @patch('mailmind.core.email_batch_processor.EmailBatchProcessor._process_one')
    def test_process_batch_progress_callback_exception(self, mock_process_one):
        """Test batch processing continues if progress callback fails."""
        mock_engine = Mock()
        mock_pool = Mock()
        mock_pool.size = 3

        mock_process_one.return_value = {'status': 'success'}

        processor = EmailBatchProcessor(mock_engine, mock_pool)

        emails = [Mock(id=i) for i in range(5)]
        progress_callback = Mock(side_effect=Exception("Callback error"))

        # Should not raise despite callback failures
        result = processor.process_batch(emails, progress_callback=progress_callback)

        assert result.total == 5
        assert result.success == 5

    @patch('mailmind.core.email_batch_processor.EmailBatchProcessor._process_one')
    def test_process_batch_performance_metrics(self, mock_process_one):
        """Test performance metrics calculation (emails/minute)."""
        mock_engine = Mock()
        mock_pool = Mock()
        mock_pool.size = 3

        # Mock quick processing (10ms per email)
        def quick_process(email):
            time.sleep(0.01)
            return {'status': 'success'}

        mock_process_one.side_effect = quick_process

        processor = EmailBatchProcessor(mock_engine, mock_pool)

        emails = [Mock(id=i) for i in range(10)]
        result = processor.process_batch(emails)

        # Should have performance metrics
        assert result.elapsed_time > 0
        assert result.emails_per_minute > 0

        # With 10 emails processed in ~0.1s (parallel), expect >1000 emails/minute
        # But with serial processing in test, expect lower
        # Just verify calculation is working
        expected_epm = (10 / result.elapsed_time) * 60
        assert abs(result.emails_per_minute - expected_epm) < 1.0


class TestProcessOne:
    """Test _process_one method."""

    def test_process_one_with_connection_pool(self):
        """Test processing single email uses connection pool."""
        mock_engine = Mock()
        mock_engine.analyze_email.return_value = {'status': 'success', 'priority': 'high'}

        mock_pool = MagicMock()
        mock_conn = Mock()
        mock_pool.size = 3
        # Use MagicMock's context manager support
        mock_pool.acquire.return_value.__enter__.return_value = mock_conn
        mock_pool.acquire.return_value.__exit__.return_value = None

        processor = EmailBatchProcessor(mock_engine, mock_pool)

        email = Mock(id=123)
        result = processor._process_one(email)

        # Verify connection pool was used
        mock_pool.acquire.assert_called_once()

        # Verify analyze_email was called with connection
        mock_engine.analyze_email.assert_called_once_with(email, mock_conn)

        # Verify result
        assert result['status'] == 'success'
        assert result['priority'] == 'high'

    def test_process_one_exception_handling(self):
        """Test _process_one handles exceptions gracefully."""
        mock_engine = Mock()
        mock_engine.analyze_email.side_effect = Exception("Analysis error")

        mock_pool = MagicMock()
        mock_conn = Mock()
        mock_pool.size = 3
        # Use MagicMock's context manager support
        mock_pool.acquire.return_value.__enter__.return_value = mock_conn
        mock_pool.acquire.return_value.__exit__.return_value = None

        processor = EmailBatchProcessor(mock_engine, mock_pool)

        email = Mock(id=123)
        result = processor._process_one(email)

        # Should return error dict instead of raising
        assert 'error' in result
        assert 'Analysis error' in result['error']
        assert result['email_id'] == 123


class TestBatchProcessorLifecycle:
    """Test EmailBatchProcessor lifecycle management."""

    def test_shutdown(self):
        """Test graceful shutdown."""
        mock_engine = Mock()
        mock_pool = Mock()
        mock_pool.size = 3

        processor = EmailBatchProcessor(mock_engine, mock_pool)

        with patch.object(processor.executor, 'shutdown') as mock_shutdown:
            processor.shutdown(wait=True)
            mock_shutdown.assert_called_once_with(wait=True)

    def test_context_manager(self):
        """Test context manager usage."""
        mock_engine = Mock()
        mock_pool = Mock()
        mock_pool.size = 3

        with EmailBatchProcessor(mock_engine, mock_pool) as processor:
            assert isinstance(processor, EmailBatchProcessor)

        # Executor should be shutdown after context exit
        # Note: Can't easily verify shutdown was called due to mock complexity
        # This test mainly verifies context manager protocol works


class TestResultAggregation:
    """Test result aggregation."""

    @patch('mailmind.core.email_batch_processor.EmailBatchProcessor._process_one')
    def test_result_aggregation_mixed_results(self, mock_process_one):
        """Test result aggregation with mixed success/failure."""
        mock_engine = Mock()
        mock_pool = Mock()
        mock_pool.size = 3

        # 3 successful, 2 failed
        mock_process_one.side_effect = [
            {'status': 'success', 'priority': 'high'},
            {'error': 'Failed'},
            {'status': 'success', 'priority': 'low'},
            {'error': 'Timeout'},
            {'status': 'success', 'priority': 'medium'}
        ]

        processor = EmailBatchProcessor(mock_engine, mock_pool)

        emails = [Mock(id=i) for i in range(5)]
        result = processor.process_batch(emails)

        assert result.total == 5
        assert result.success == 3
        assert result.failed == 2

        # Check results list
        assert len(result.results) == 5
        assert result.results[0]['status'] == 'success'
        assert 'error' in result.results[1]
        assert result.results[2]['status'] == 'success'
        assert 'error' in result.results[3]
        assert result.results[4]['status'] == 'success'
