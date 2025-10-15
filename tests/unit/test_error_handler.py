"""
Unit tests for ErrorHandler class.

Tests Story 2.6 AC1: Graceful Error Handling
Tests Story 2.6 AC2: Automatic Recovery
Tests Story 2.6 AC5: User-Friendly Error Messages
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time

from mailmind.core.error_handler import ErrorHandler, retry, get_error_handler
from mailmind.core.exceptions import (
    MailMindException,
    OllamaConnectionError,
    OllamaModelError,
    OutlookNotRunningException,
    OutlookConnectionError,
    DatabaseCorruptionError,
    InsufficientMemoryError,
)


class TestErrorHandlerSingleton:
    """Test ErrorHandler singleton pattern."""

    def test_get_instance_returns_singleton(self):
        """Test ErrorHandler.get_instance() returns same instance."""
        instance1 = ErrorHandler.get_instance()
        instance2 = ErrorHandler.get_instance()
        assert instance1 is instance2

    def test_get_error_handler_convenience_function(self):
        """Test get_error_handler() convenience function."""
        handler = get_error_handler()
        assert isinstance(handler, ErrorHandler)
        assert handler is ErrorHandler.get_instance()


class TestRetryDecorator:
    """Test retry decorator with exponential backoff."""

    def test_retry_succeeds_on_first_attempt(self):
        """Test function succeeds on first attempt (no retries)."""
        mock_func = Mock(return_value="success")

        @retry(max_retries=3, initial_delay=0.01)
        def test_function():
            return mock_func()

        result = test_function()
        assert result == "success"
        assert mock_func.call_count == 1

    def test_retry_succeeds_after_failures(self):
        """Test function succeeds after several failures."""
        call_count = 0

        @retry(max_retries=5, initial_delay=0.01, exceptions=(ValueError,))
        def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Not yet")
            return "success"

        result = test_function()
        assert result == "success"
        assert call_count == 3

    def test_retry_exhausts_attempts(self):
        """Test retry raises exception after max attempts."""
        @retry(max_retries=3, initial_delay=0.01, exceptions=(ValueError,))
        def test_function():
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            test_function()

    def test_retry_exponential_backoff(self):
        """Test retry uses exponential backoff timing."""
        call_times = []

        @retry(max_retries=3, initial_delay=0.1, backoff_multiplier=2.0, exceptions=(ValueError,))
        def test_function():
            call_times.append(time.time())
            raise ValueError("Fail")

        with pytest.raises(ValueError):
            test_function()

        # Check delays between attempts (approx 0.1s, 0.2s, 0.4s)
        assert len(call_times) == 4  # Initial + 3 retries
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]
        delay3 = call_times[3] - call_times[2]

        assert 0.08 < delay1 < 0.15  # ~0.1s
        assert 0.18 < delay2 < 0.25  # ~0.2s
        assert 0.38 < delay3 < 0.45  # ~0.4s

    def test_retry_max_delay_cap(self):
        """Test retry respects max_delay cap."""
        @retry(max_retries=5, initial_delay=0.1, backoff_multiplier=10.0, max_delay=0.3, exceptions=(ValueError,))
        def test_function():
            raise ValueError("Fail")

        start_time = time.time()
        with pytest.raises(ValueError):
            test_function()
        elapsed = time.time() - start_time

        # With max_delay=0.3s, total time should be < 5 * 0.3s = 1.5s
        # (Without cap, would be 0.1 + 1.0 + 10.0 + ... = huge)
        assert elapsed < 2.0

    def test_retry_only_catches_specified_exceptions(self):
        """Test retry only catches exceptions in exceptions tuple."""
        @retry(max_retries=3, initial_delay=0.01, exceptions=(ValueError,))
        def test_function():
            raise TypeError("Different exception")

        # TypeError not in exceptions tuple, should be raised immediately
        with pytest.raises(TypeError, match="Different exception"):
            test_function()


class TestErrorHandlerExceptionHandling:
    """Test ErrorHandler exception handling."""

    def test_handle_mailmind_exception(self):
        """Test handling MailMindException with user_message."""
        handler = ErrorHandler.get_instance()
        exception = OllamaConnectionError(technical_details="Ollama not running")

        user_message = handler.handle_exception(exception)

        assert "Ollama" in user_message
        assert "https://ollama.ai/download" in user_message

    def test_handle_generic_exception(self):
        """Test handling generic Exception without user_message."""
        handler = ErrorHandler.get_instance()
        exception = RuntimeError("Generic error")

        user_message = handler.handle_exception(exception)

        assert "unexpected error" in user_message.lower()
        assert "RuntimeError" in user_message

    def test_handle_exception_with_context(self):
        """Test handling exception with context logging."""
        handler = ErrorHandler.get_instance()
        exception = ValueError("Test error")
        context = {"operation": "test_op", "user": "test_user"}

        with patch.object(handler, 'log_error') as mock_log:
            handler.handle_exception(exception, context)
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            # log_error is called with positional args: (exception, "ERROR", context)
            assert call_args[0][0] is exception
            assert call_args[0][2] == context

    def test_handle_exception_updates_stats(self):
        """Test handling exception updates error statistics."""
        handler = ErrorHandler.get_instance()
        # Clear stats
        handler.error_stats.clear()

        exception1 = ValueError("Error 1")
        exception2 = ValueError("Error 2")
        exception3 = TypeError("Error 3")

        handler.handle_exception(exception1)
        handler.handle_exception(exception2)
        handler.handle_exception(exception3)

        stats = handler.get_error_stats()
        assert stats.get("ValueError") == 2
        assert stats.get("TypeError") == 1


class TestRecoveryStrategies:
    """Test error recovery strategies."""

    def test_register_recovery_strategy(self):
        """Test registering custom recovery strategy."""
        handler = ErrorHandler.get_instance()
        mock_strategy = Mock(return_value=True)

        handler.register_recovery_strategy(ValueError, mock_strategy)

        strategy = handler.get_recovery_strategy(ValueError)
        assert strategy is mock_strategy

    def test_recovery_strategy_called_on_exception(self):
        """Test recovery strategy is called when exception occurs."""
        handler = ErrorHandler.get_instance()
        mock_strategy = Mock(return_value=True)

        handler.register_recovery_strategy(OllamaConnectionError, mock_strategy)

        exception = OllamaConnectionError(technical_details="Test")
        handler.handle_exception(exception)

        mock_strategy.assert_called_once()

    def test_recovery_strategy_outlook_not_running(self):
        """Test recovery strategy for Outlook not running."""
        handler = ErrorHandler.get_instance()

        exception = OutlookNotRunningException(technical_details="Outlook.exe not found")
        # Recovery should prompt user (returns False - not automatic)
        success = handler._strategy_prompt_start_outlook(exception)

        assert success is False  # Requires user action

    def test_recovery_strategy_insufficient_memory(self):
        """Test recovery strategy for insufficient memory."""
        handler = ErrorHandler.get_instance()

        exception = InsufficientMemoryError(
            available_gb=1.5,
            required_gb=2.0,
            technical_details="Low memory"
        )
        # Recovery should trigger memory optimization
        success = handler._strategy_reduce_memory_usage(exception)

        # Returns False (requires external optimization components)
        assert success is False


class TestErrorLogging:
    """Test error logging functionality."""

    def test_log_error_with_severity(self):
        """Test logging error with different severity levels."""
        handler = ErrorHandler.get_instance()
        exception = ValueError("Test error")

        with patch('mailmind.core.error_handler.logger') as mock_logger:
            handler.log_error(exception, "WARNING")
            mock_logger.warning.assert_called_once()

            handler.log_error(exception, "ERROR")
            mock_logger.error.assert_called_once()

            handler.log_error(exception, "CRITICAL")
            mock_logger.critical.assert_called_once()

    def test_log_error_includes_context(self):
        """Test error logging includes context information."""
        handler = ErrorHandler.get_instance()
        exception = ValueError("Test error")
        context = {"operation": "test", "file": "test.py"}

        with patch('mailmind.core.error_handler.logger') as mock_logger:
            handler.log_error(exception, "ERROR", context)

            # Check that context was included in log message
            call_args = mock_logger.error.call_args
            log_message = call_args[0][0]
            assert "operation=test" in log_message
            assert "file=test.py" in log_message

    def test_log_error_includes_stack_trace(self):
        """Test error logging includes stack trace for ERROR+ levels."""
        handler = ErrorHandler.get_instance()
        exception = RuntimeError("Test error")

        with patch('mailmind.core.error_handler.logger') as mock_logger:
            handler.log_error(exception, "ERROR")

            # Check exc_info parameter was passed
            call_kwargs = mock_logger.error.call_args[1]
            assert call_kwargs.get('exc_info') is True


class TestUserMessages:
    """Test user-friendly error messages."""

    def test_ollama_connection_error_message(self):
        """Test OllamaConnectionError has user-friendly message."""
        exception = OllamaConnectionError(technical_details="Connection refused")

        assert "Ollama" in exception.user_message
        assert "https://ollama.ai/download" in exception.user_message
        assert not "Connection refused" in exception.user_message  # No technical jargon

    def test_ollama_model_error_message(self):
        """Test OllamaModelError has user-friendly message."""
        exception = OllamaModelError(
            model_name="llama3.1:8b-instruct-q4_K_M",
            technical_details="Model not found"
        )

        assert "llama3.1:8b-instruct-q4_K_M" in exception.user_message
        assert "ollama pull" in exception.user_message
        assert "10-20 minutes" in exception.user_message

    def test_outlook_not_running_error_message(self):
        """Test OutlookNotRunningException has user-friendly message."""
        exception = OutlookNotRunningException(technical_details="Process not found")

        assert "Outlook" in exception.user_message
        assert "start" in exception.user_message.lower()
        assert not "Process not found" in exception.user_message

    def test_insufficient_memory_error_message(self):
        """Test InsufficientMemoryError has user-friendly message."""
        exception = InsufficientMemoryError(
            available_gb=1.8,
            required_gb=2.0,
            technical_details="psutil: 1.8GB available"
        )

        assert "1.8" in exception.user_message or "1.8GB" in exception.user_message
        assert "close" in exception.user_message.lower()
        assert "applications" in exception.user_message.lower()

    def test_database_corruption_error_message(self):
        """Test DatabaseCorruptionError has user-friendly message."""
        exception = DatabaseCorruptionError(technical_details="sqlite3: database disk image is malformed")

        assert "corruption" in exception.user_message.lower()
        assert "backup" in exception.user_message.lower()
        assert not "disk image" in exception.user_message  # No technical jargon


class TestUICallbackIntegration:
    """Test UI callback integration."""

    def test_set_ui_callback(self):
        """Test setting UI callback."""
        handler = ErrorHandler.get_instance()
        mock_callback = Mock()

        handler.set_ui_callback(mock_callback)

        assert handler.ui_callback is mock_callback

    def test_show_error_dialog_calls_callback(self):
        """Test show_error_dialog calls UI callback."""
        handler = ErrorHandler.get_instance()
        mock_callback = Mock()
        handler.set_ui_callback(mock_callback)

        handler.show_error_dialog("Test message", "Test details", True)

        mock_callback.assert_called_once_with("Test message", "Test details", True)

    def test_show_error_dialog_without_callback(self):
        """Test show_error_dialog handles missing callback gracefully."""
        handler = ErrorHandler.get_instance()
        handler.ui_callback = None  # No callback set

        # Should not raise exception
        handler.show_error_dialog("Test message", "Test details", True)


class TestErrorStats:
    """Test error statistics tracking."""

    def test_get_error_stats_empty(self):
        """Test get_error_stats returns empty dict initially."""
        handler = ErrorHandler.get_instance()
        handler.error_stats.clear()

        stats = handler.get_error_stats()
        assert stats == {}

    def test_get_error_stats_tracking(self):
        """Test error stats are tracked correctly."""
        handler = ErrorHandler.get_instance()
        handler.error_stats.clear()

        # Simulate several errors
        handler.handle_exception(ValueError("Error 1"))
        handler.handle_exception(ValueError("Error 2"))
        handler.handle_exception(TypeError("Error 3"))
        handler.handle_exception(RuntimeError("Error 4"))
        handler.handle_exception(ValueError("Error 5"))

        stats = handler.get_error_stats()
        assert stats["ValueError"] == 3
        assert stats["TypeError"] == 1
        assert stats["RuntimeError"] == 1
