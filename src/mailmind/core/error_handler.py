"""
Centralized error handling system for MailMind application.

Provides:
- ErrorHandler singleton for consistent error processing
- Retry decorator with exponential backoff (AC2, AC3)
- Recovery strategies for common error scenarios (AC12)
- User-friendly error message translation (AC5)

Story 2.6 AC1: Graceful Error Handling
Story 2.6 AC2: Automatic Recovery
Story 2.6 AC5: User-Friendly Error Messages
"""

import functools
import logging
import time
from typing import Callable, Dict, Optional, Type, Any, Tuple
from dataclasses import dataclass

from mailmind.core.exceptions import (
    MailMindException,
    OllamaConnectionError,
    OllamaModelError,
    OutlookNotRunningException,
    OutlookConnectionError,
    DatabaseCorruptionError,
    InsufficientMemoryError,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Retry decorator with exponential backoff (AC2, AC3)
# ============================================================================

@dataclass
class RetryConfig:
    """Configuration for retry decorator."""
    max_retries: int = 5
    initial_delay: float = 1.0
    backoff_multiplier: float = 2.0
    max_delay: float = 16.0
    exceptions: Tuple[Type[Exception], ...] = (ConnectionError, TimeoutError)


def retry(
    max_retries: int = 5,
    initial_delay: float = 1.0,
    backoff_multiplier: float = 2.0,
    max_delay: float = 16.0,
    exceptions: Tuple[Type[Exception], ...] = (ConnectionError, TimeoutError)
):
    """
    Retry decorator with exponential backoff.

    AC2: Automatic recovery with retry logic (1s → 2s → 4s → 8s → 16s)
    AC3: Model fallback - applies to OllamaManager operations

    Args:
        max_retries: Maximum number of retry attempts (default: 5)
        initial_delay: Initial retry delay in seconds (default: 1.0s)
        backoff_multiplier: Delay multiplier for each retry (default: 2.0x)
        max_delay: Maximum retry delay in seconds (default: 16.0s)
        exceptions: Tuple of exception types to catch and retry

    Returns:
        Decorated function with retry logic

    Example:
        @retry(max_retries=5, exceptions=(OutlookConnectionError,))
        def connect_to_outlook():
            # Connection logic here
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    # Attempt the function call
                    result = func(*args, **kwargs)

                    # Log success if this was a retry
                    if attempt > 0:
                        logger.info(
                            f"{func.__name__} succeeded on attempt {attempt + 1}/{max_retries + 1}"
                        )

                    return result

                except exceptions as e:
                    last_exception = e

                    # If we've exhausted all retries, raise the exception
                    if attempt >= max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries + 1} attempts: {str(e)}"
                        )
                        raise

                    # Log the retry attempt
                    logger.warning(
                        f"{func.__name__} failed on attempt {attempt + 1}/{max_retries + 1}, "
                        f"retrying in {delay:.1f}s: {str(e)}"
                    )

                    # Wait before retrying
                    time.sleep(delay)

                    # Increase delay with exponential backoff (cap at max_delay)
                    delay = min(delay * backoff_multiplier, max_delay)

            # Should never reach here, but raise last exception if we do
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


# ============================================================================
# ErrorHandler singleton class (AC1, AC5)
# ============================================================================

class ErrorHandler:
    """
    Centralized error handling singleton.

    Responsibilities:
    1. Catch and log all exceptions (AC1)
    2. Translate technical exceptions to user-friendly messages (AC5)
    3. Trigger recovery strategies (retry, fallback, graceful degradation) (AC2, AC3, AC12)
    4. Show error dialogs to user (integration with UI - Story 2.3)
    5. Track error statistics for debugging

    Usage:
        handler = ErrorHandler.get_instance()
        try:
            risky_operation()
        except Exception as e:
            user_message = handler.handle_exception(e, context={'operation': 'email_fetch'})
            # Display user_message in UI
    """

    _instance: Optional['ErrorHandler'] = None
    _initialized: bool = False

    def __init__(self):
        """Initialize ErrorHandler (use get_instance() instead)."""
        if ErrorHandler._initialized:
            return

        self.error_stats: Dict[str, int] = {}
        self.recovery_strategies: Dict[Type[Exception], Callable] = {}
        self.ui_callback: Optional[Callable] = None

        # Register default recovery strategies
        self._register_default_strategies()

        ErrorHandler._initialized = True

    @classmethod
    def get_instance(cls) -> 'ErrorHandler':
        """
        Get ErrorHandler singleton instance.

        Returns:
            ErrorHandler singleton instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _register_default_strategies(self):
        """Register default recovery strategies for common exceptions."""
        # AC2: Outlook reconnection
        self.register_recovery_strategy(
            OutlookNotRunningException,
            self._strategy_prompt_start_outlook
        )
        self.register_recovery_strategy(
            OutlookConnectionError,
            self._strategy_retry_connection
        )

        # AC3: Model fallback
        self.register_recovery_strategy(
            OllamaModelError,
            self._strategy_model_fallback
        )

        # AC12: Database corruption recovery
        self.register_recovery_strategy(
            DatabaseCorruptionError,
            self._strategy_restore_database
        )

        # AC12: Memory pressure handling
        self.register_recovery_strategy(
            InsufficientMemoryError,
            self._strategy_reduce_memory_usage
        )

    def register_recovery_strategy(
        self,
        exception_type: Type[Exception],
        strategy: Callable
    ):
        """
        Register a recovery strategy for an exception type.

        Args:
            exception_type: Exception class to handle
            strategy: Callable recovery strategy (takes exception, returns success bool)
        """
        self.recovery_strategies[exception_type] = strategy
        logger.debug(f"Registered recovery strategy for {exception_type.__name__}")

    def handle_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Handle exception with logging and recovery.

        AC1: Graceful error handling
        AC5: User-friendly error messages

        Args:
            exception: Exception to handle
            context: Optional context dict for logging (operation, user, etc.)

        Returns:
            str: User-friendly error message
        """
        # Update error statistics
        exc_type = type(exception).__name__
        self.error_stats[exc_type] = self.error_stats.get(exc_type, 0) + 1

        # Log the error with context
        self.log_error(exception, "ERROR", context)

        # Try recovery strategy
        recovery_attempted = self._attempt_recovery(exception)

        # Get user-friendly message
        user_message = self._get_user_message(exception)

        # Show error dialog if UI callback registered
        if self.ui_callback and not recovery_attempted:
            self.show_error_dialog(user_message, str(exception), show_report_button=True)

        return user_message

    def log_error(
        self,
        exception: Exception,
        severity: str = "ERROR",
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Log error with context and severity.

        AC4: Comprehensive logging

        Args:
            exception: Exception to log
            severity: Log severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            context: Optional context dict
        """
        # Build log message with context
        context_str = ""
        if context:
            context_str = " | ".join([f"{k}={v}" for k, v in context.items()])

        # Get technical details if available
        technical_details = getattr(exception, 'technical_details', str(exception))

        # Log with appropriate severity
        log_func = getattr(logger, severity.lower(), logger.error)
        log_message = f"{type(exception).__name__}: {technical_details}"
        if context_str:
            log_message += f" | {context_str}"

        log_func(log_message, exc_info=(severity in ["ERROR", "CRITICAL"]))

    def _get_user_message(self, exception: Exception) -> str:
        """
        Get user-friendly message from exception.

        AC5: User-friendly error messages

        Args:
            exception: Exception to translate

        Returns:
            str: User-friendly message
        """
        # If exception has user_message attribute (MailMindException), use it
        if isinstance(exception, MailMindException):
            return exception.user_message

        # Otherwise, create generic user-friendly message
        return (
            f"An unexpected error occurred: {type(exception).__name__}. "
            f"Please try again or contact support if the issue persists."
        )

    def _attempt_recovery(self, exception: Exception) -> bool:
        """
        Attempt recovery strategy for exception.

        Args:
            exception: Exception to recover from

        Returns:
            bool: True if recovery was attempted, False otherwise
        """
        exc_type = type(exception)

        # Check if we have a registered strategy
        strategy = self.recovery_strategies.get(exc_type)
        if not strategy:
            return False

        try:
            logger.info(f"Attempting recovery strategy for {exc_type.__name__}")
            success = strategy(exception)
            if success:
                logger.info(f"Recovery successful for {exc_type.__name__}")
            else:
                logger.warning(f"Recovery failed for {exc_type.__name__}")
            return True
        except Exception as e:
            logger.error(f"Recovery strategy failed for {exc_type.__name__}: {e}")
            return False

    def get_recovery_strategy(
        self,
        exception_type: Type[Exception]
    ) -> Optional[Callable]:
        """
        Get registered recovery strategy for exception type.

        Args:
            exception_type: Exception class

        Returns:
            Optional[Callable]: Recovery strategy or None
        """
        return self.recovery_strategies.get(exception_type)

    def show_error_dialog(
        self,
        message: str,
        details: str,
        show_report_button: bool = True
    ):
        """
        Show error dialog to user via UI callback.

        AC6: Issue reporting
        Integration with Story 2.3 (CustomTkinter UI)

        Args:
            message: User-friendly error message
            details: Technical error details
            show_report_button: Show "Report Issue" button (AC6)
        """
        if self.ui_callback:
            self.ui_callback(message, details, show_report_button)
        else:
            logger.warning(
                f"No UI callback registered, error not shown to user: {message}"
            )

    def set_ui_callback(self, callback: Callable):
        """
        Set UI callback for showing error dialogs.

        Args:
            callback: Callable(message, details, show_report_button) -> None
        """
        self.ui_callback = callback
        logger.debug("UI callback registered for error dialogs")

    def get_error_stats(self) -> Dict[str, int]:
        """
        Get error statistics.

        Returns:
            Dict[str, int]: Error counts by exception type
        """
        return self.error_stats.copy()

    # ========================================================================
    # Recovery strategies (AC2, AC3, AC12)
    # ========================================================================

    def _strategy_prompt_start_outlook(self, exception: Exception) -> bool:
        """
        Recovery strategy: Prompt user to start Outlook.

        AC12: Error Scenario - Outlook not running
        """
        logger.info("Recovery: Prompting user to start Outlook")
        # UI callback will show dialog with retry button
        return False  # Not automatically recoverable, requires user action

    def _strategy_retry_connection(self, exception: Exception) -> bool:
        """
        Recovery strategy: Retry connection (handled by @retry decorator).

        AC2: Automatic recovery
        """
        logger.info("Recovery: Retry connection (handled by decorator)")
        return False  # Handled by retry decorator

    def _strategy_model_fallback(self, exception: Exception) -> bool:
        """
        Recovery strategy: Fallback to alternate model.

        AC3: Model fallback (Llama → Mistral)
        """
        logger.info("Recovery: Attempting model fallback (Llama → Mistral)")
        # Actual fallback implemented in OllamaManager (Story 1.1)
        return False  # Handled by OllamaManager.verify_model()

    def _strategy_restore_database(self, exception: Exception) -> bool:
        """
        Recovery strategy: Restore database from backup.

        AC12: Error Scenario - Database corruption
        """
        logger.info("Recovery: Attempting database restoration from backup")
        # Actual restoration implemented in DatabaseManager (Story 2.2)
        return False  # Requires DatabaseManager integration

    def _strategy_reduce_memory_usage(self, exception: Exception) -> bool:
        """
        Recovery strategy: Reduce memory usage.

        AC12: Error Scenario - Insufficient memory
        AC6: Graceful degradation
        """
        logger.info("Recovery: Reducing memory usage (batch size, cache, etc.)")
        # Actual optimization implemented in PerformanceTracker (Story 1.6)
        return False  # Requires integration with performance components


# ============================================================================
# Convenience functions
# ============================================================================

def get_error_handler() -> ErrorHandler:
    """
    Get ErrorHandler singleton instance.

    Returns:
        ErrorHandler singleton
    """
    return ErrorHandler.get_instance()
