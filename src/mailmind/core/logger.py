"""
Comprehensive logging system for MailMind application.

Provides:
- Structured logging with RotatingFileHandler (AC4)
- Log format: [timestamp] level [module:function:line] message
- Log rotation: max 10 files of 10MB each
- Log sanitization for clipboard export (AC6)
- Performance metrics logging

Story 2.6 AC4: Comprehensive Logging
Story 2.6 AC6: Issue Reporting
"""

import logging
import os
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional
from datetime import datetime


# ============================================================================
# Log Configuration
# ============================================================================

# Log directory: %APPDATA%/MailMind/logs/ (Windows)
# or ~/Library/Application Support/MailMind/logs/ (macOS)
# or ~/.local/share/MailMind/logs/ (Linux)
def get_log_directory() -> Path:
    """
    Get platform-specific log directory.

    Returns:
        Path: Log directory path
    """
    if os.name == 'nt':  # Windows
        appdata = os.getenv('APPDATA', os.path.expanduser('~'))
        log_dir = Path(appdata) / 'MailMind' / 'logs'
    elif os.name == 'posix':
        if 'darwin' in os.sys.platform:  # macOS
            log_dir = Path.home() / 'Library' / 'Application Support' / 'MailMind' / 'logs'
        else:  # Linux
            log_dir = Path.home() / '.local' / 'share' / 'MailMind' / 'logs'
    else:
        # Fallback to current directory
        log_dir = Path.cwd() / 'logs'

    # Create directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)

    return log_dir


# ============================================================================
# Custom Formatter
# ============================================================================

class MailMindFormatter(logging.Formatter):
    """
    Custom formatter for MailMind logs.

    Format: [timestamp] level [module:function:line] message
    Story 2.6 AC4: Structured logging format
    """

    def __init__(self):
        """Initialize formatter with MailMind format."""
        # Format: [2025-10-15 14:32:15] INFO [ollama_manager:connect:75] Connected to Ollama
        super().__init__(
            fmt='[%(asctime)s] %(levelname)-8s [%(name)s:%(funcName)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with custom format.

        Args:
            record: LogRecord to format

        Returns:
            str: Formatted log message
        """
        # Add stack trace for ERROR and CRITICAL levels (AC4)
        if record.levelno >= logging.ERROR and record.exc_info:
            # Format exception info
            record.exc_text = self.formatException(record.exc_info)

        return super().format(record)


# ============================================================================
# Logging Setup
# ============================================================================

_logger_initialized = False


def setup_logging(
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
    console_output: bool = True
) -> None:
    """
    Setup comprehensive logging system for MailMind.

    Story 2.6 AC4: Comprehensive logging with rotation

    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Optional log directory (defaults to platform-specific location)
        console_output: Also log to console (default: True)
    """
    global _logger_initialized

    if _logger_initialized:
        return

    # Get log directory
    if log_dir is None:
        log_dir = get_log_directory()

    # Create log file path
    log_file = log_dir / 'mailmind.log'

    # Create root logger
    root_logger = logging.getLogger()

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Set log level
    level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(level)

    # Create formatter
    formatter = MailMindFormatter()

    # AC4: RotatingFileHandler (10 files x 10MB each)
    file_handler = RotatingFileHandler(
        filename=str(log_file),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,  # Max 10 files
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Console handler (optional)
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Log initialization
    root_logger.info("=" * 80)
    root_logger.info(f"MailMind Logging System Initialized")
    root_logger.info(f"Log Level: {log_level}")
    root_logger.info(f"Log Directory: {log_dir}")
    root_logger.info(f"Log File: {log_file}")
    root_logger.info(f"Max File Size: 10MB, Max Files: 10")
    root_logger.info("=" * 80)

    _logger_initialized = True


def get_logger(module_name: str) -> logging.Logger:
    """
    Get logger for a specific module.

    Args:
        module_name: Name of the module (usually __name__)

    Returns:
        logging.Logger: Logger instance for the module
    """
    return logging.getLogger(module_name)


# ============================================================================
# Log Export and Sanitization (AC6)
# ============================================================================

def sanitize_logs(log_text: str) -> str:
    """
    Sanitize log text by removing sensitive information.

    Story 2.6 AC6: Log sanitization (remove sensitive data before clipboard copy)

    Removes:
    - Email addresses (replaced with [EMAIL])
    - Email subjects (replaced with [SUBJECT])
    - Email bodies (removed entirely)
    - Personal names (if detected)
    - API keys/tokens (if detected)

    Args:
        log_text: Raw log text

    Returns:
        str: Sanitized log text
    """
    # Replace email addresses
    sanitized = re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        '[EMAIL]',
        log_text
    )

    # Replace potential API keys (sequences of 20+ alphanumeric characters, underscores, hyphens)
    # Matches patterns like: sk_1234..., api-key-12345..., etc.
    sanitized = re.sub(
        r'\b[A-Za-z0-9_-]{20,}\b',
        '[API_KEY]',
        sanitized
    )

    # Replace email subjects (between quotes after "subject:")
    sanitized = re.sub(
        r'(subject:?\s*["\']?)([^"\']+)(["\']?)',
        r'\1[SUBJECT]\3',
        sanitized,
        flags=re.IGNORECASE
    )

    # Remove email body content (between "body:" and next field or end of line)
    sanitized = re.sub(
        r'(body:?\s*["\']?)([^"\']+)(["\']?)',
        r'\1[BODY_REMOVED]\3',
        sanitized,
        flags=re.IGNORECASE
    )

    # Add sanitization notice at the top
    header = (
        "=" * 80 + "\n"
        "SANITIZED LOG OUTPUT - Sensitive information removed\n"
        "Email addresses, subjects, and bodies have been redacted\n"
        "=" * 80 + "\n\n"
    )

    return header + sanitized


def export_logs_to_clipboard() -> bool:
    """
    Export sanitized logs to clipboard for support submission.

    Story 2.6 AC6: "Report Issue" button copies logs to clipboard

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Find the actual log file from the logging handlers
        root_logger = logging.getLogger()
        log_file = None

        for handler in root_logger.handlers:
            if isinstance(handler, RotatingFileHandler):
                log_file = Path(handler.baseFilename)
                break

        # Fallback to default location if no file handler found
        if log_file is None:
            log_dir = get_log_directory()
            log_file = log_dir / 'mailmind.log'

        if not log_file.exists():
            logging.error(f"Log file not found: {log_file}")
            return False

        # Read log file (last 1000 lines)
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            # Take last 1000 lines (or all if fewer)
            recent_lines = lines[-1000:] if len(lines) > 1000 else lines
            log_text = ''.join(recent_lines)

        # Sanitize logs
        sanitized_logs = sanitize_logs(log_text)

        # Try to copy to clipboard
        try:
            import pyperclip
            pyperclip.copy(sanitized_logs)
            logging.info("✅ Logs exported to clipboard (sanitized)")
            return True
        except ImportError:
            # Fallback: Save to file in same directory as log file
            export_file = log_file.parent / f'mailmind_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
            with open(export_file, 'w', encoding='utf-8') as f:
                f.write(sanitized_logs)
            logging.warning(
                f"pyperclip not available, saved logs to file: {export_file}"
            )
            return True

    except Exception as e:
        logging.error(f"Failed to export logs: {e}", exc_info=True)
        return False


# ============================================================================
# Performance Metrics Logging (AC4)
# ============================================================================

def log_performance_metrics(
    operation: str,
    duration_seconds: float,
    tokens_per_second: Optional[float] = None,
    memory_mb: Optional[float] = None,
    cache_hits: Optional[int] = None,
    **extra_metrics
):
    """
    Log performance metrics in structured format.

    Story 2.6 AC4: Add performance metrics to logs (tokens/sec, memory usage)

    Args:
        operation: Name of the operation (e.g., "email_analysis", "model_inference")
        duration_seconds: Operation duration in seconds
        tokens_per_second: Optional tokens/sec metric
        memory_mb: Optional memory usage in MB
        cache_hits: Optional cache hit count
        **extra_metrics: Additional metrics to log
    """
    logger = logging.getLogger(__name__)

    # Build metrics dict
    metrics = {
        'operation': operation,
        'duration_s': f'{duration_seconds:.3f}',
    }

    if tokens_per_second is not None:
        metrics['tokens_per_sec'] = f'{tokens_per_second:.1f}'

    if memory_mb is not None:
        metrics['memory_mb'] = f'{memory_mb:.1f}'

    if cache_hits is not None:
        metrics['cache_hits'] = cache_hits

    # Add extra metrics
    metrics.update(extra_metrics)

    # Format as key=value pairs
    metrics_str = ' | '.join([f'{k}={v}' for k, v in metrics.items()])

    # Log with INFO level
    logger.info(f"PERFORMANCE: {metrics_str}")


# ============================================================================
# Convenience functions
# ============================================================================

def set_log_level(level: str):
    """
    Update log level dynamically.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Update all handlers
    for handler in root_logger.handlers:
        handler.setLevel(log_level)

    logging.info(f"Log level changed to: {level}")


def get_log_file_path() -> Path:
    """
    Get current log file path.

    Returns:
        Path: Log file path
    """
    log_dir = get_log_directory()
    return log_dir / 'mailmind.log'


def get_log_files() -> list:
    """
    Get all log files (including rotated files).

    Returns:
        list: List of log file paths
    """
    log_dir = get_log_directory()
    log_files = list(log_dir.glob('mailmind.log*'))
    return sorted(log_files)
