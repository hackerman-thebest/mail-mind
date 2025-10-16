"""
Security Event Logger for MailMind

Story 3.2 AC3: Security Event Logging
Logs all security events to dedicated security.log with rotation (max 10 files of 10MB).

This module provides dedicated security event logging with:
- Dedicated security.log file (separate from application logs)
- Automatic log rotation (10 files × 10MB each)
- Structured log format with timestamp, level, pattern, metadata, action
- Integration with existing logging infrastructure from Story 2.6

Log Format:
    2025-10-16 14:30:45,123 | WARNING | blocked | pattern=ignore_instructions |
    severity=high | subject="Urgent!" | sender="attacker@evil.com" |
    message_id="abc123" | action=blocked_email

Example Usage:
    logger = SecurityLogger()
    logger.log_event(
        event_type="blocked",
        pattern_name="ignore_instructions",
        email_metadata={"subject": "...", "sender": "...", "message_id": "..."},
        action_taken="blocked_email",
        severity="high"
    )
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Dict, Optional
from datetime import datetime


class SecurityLogger:
    """
    Dedicated security event logger with rotation.

    Story 3.2 AC3: Security Event Logging

    This class provides a dedicated logger for security events with:
    - Dedicated security.log file
    - Automatic rotation (10 files × 10MB each)
    - Structured log format

    Attributes:
        logger: Python logging.Logger instance
        log_file_path: Path to security.log file
    """

    def __init__(self, log_dir: str = None):
        """
        Initialize SecurityLogger with rotating file handler.

        Args:
            log_dir: Directory for security.log (default: data/logs/)
        """
        # Determine log directory
        if log_dir is None:
            # Default to data/logs/ in project root
            # Assuming we're in src/mailmind/core/, go up 3 levels
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            log_dir = os.path.join(project_root, "data", "logs")

        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)

        self.log_file_path = os.path.join(log_dir, "security.log")

        # Create dedicated logger for security events
        self.logger = logging.getLogger("mailmind.security")
        self.logger.setLevel(logging.INFO)

        # Prevent duplicate handlers if SecurityLogger is instantiated multiple times
        if not self.logger.handlers:
            # Create rotating file handler
            # Story 2.6: Log rotation (10 files × 10MB)
            handler = RotatingFileHandler(
                self.log_file_path,
                maxBytes=10 * 1024 * 1024,  # 10MB per file
                backupCount=10,  # Keep 10 backup files
                encoding='utf-8'
            )

            # Define structured log format
            # Format: timestamp | level | event_type | pattern=X | severity=X | subject=X | sender=X | action=X
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)

            self.logger.addHandler(handler)

        logging.info(f"SecurityLogger initialized: {self.log_file_path}")

    def log_event(
        self,
        event_type: str,
        pattern_name: str,
        email_metadata: Dict[str, str],
        action_taken: str,
        severity: str = "high"
    ):
        """
        Log a security event to security.log.

        Story 3.2 AC3: Security Event Logging

        Args:
            event_type: Type of event ("blocked", "warned", "override")
            pattern_name: Name of the security pattern that triggered the event
            email_metadata: Dict with subject, sender, message_id
            action_taken: Action taken ("blocked_email", "allowed_with_warning", "user_override")
            severity: Severity level ("high", "medium", "low")

        Example:
            logger.log_event(
                event_type="blocked",
                pattern_name="ignore_instructions",
                email_metadata={
                    "subject": "Urgent request!",
                    "sender": "attacker@evil.com",
                    "message_id": "abc123xyz"
                },
                action_taken="blocked_email",
                severity="high"
            )

        Log Output:
            2025-10-16 14:30:45 | WARNING | blocked | pattern=ignore_instructions |
            severity=high | subject="Urgent request!" | sender="attacker@evil.com" |
            message_id="abc123xyz" | action=blocked_email
        """
        # Extract email metadata (handle missing fields gracefully)
        subject = email_metadata.get("subject", "(No Subject)")
        sender = email_metadata.get("from", email_metadata.get("sender", "unknown"))
        message_id = email_metadata.get("message_id", "unknown")

        # Build structured log message
        log_message = (
            f"{event_type} | "
            f"pattern={pattern_name} | "
            f"severity={severity} | "
            f'subject="{subject}" | '
            f'sender="{sender}" | '
            f'message_id="{message_id}" | '
            f"action={action_taken}"
        )

        # Log at appropriate level based on event type
        if event_type == "blocked":
            self.logger.warning(log_message)
        elif event_type == "override":
            self.logger.warning(f"{log_message} | **USER OVERRIDE**")
        elif event_type == "warned":
            self.logger.info(log_message)
        else:
            self.logger.info(log_message)

    def log_override(
        self,
        pattern_name: str,
        email_metadata: Dict[str, str],
        user_confirmation: bool,
        severity: str = "high"
    ):
        """
        Log a security override event (when user bypasses blocking).

        Story 3.2 AC8: Override Option (logging requirement)

        Args:
            pattern_name: Pattern that was overridden
            email_metadata: Email metadata dict
            user_confirmation: Whether user explicitly confirmed override
            severity: Original severity level that was overridden
        """
        self.log_event(
            event_type="override",
            pattern_name=pattern_name,
            email_metadata=email_metadata,
            action_taken=f"user_override (confirmed={user_confirmation})",
            severity=severity
        )

    def get_recent_events(self, count: int = 100) -> list:
        """
        Retrieve recent security events from log file.

        Args:
            count: Number of recent events to retrieve

        Returns:
            List of log line strings (most recent first)
        """
        try:
            if not os.path.exists(self.log_file_path):
                return []

            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Return most recent N lines (reversed)
            return lines[-count:][::-1]
        except Exception as e:
            logging.error(f"Failed to read security log: {e}")
            return []

    def get_log_file_size(self) -> int:
        """
        Get current security.log file size in bytes.

        Returns:
            File size in bytes, or 0 if file doesn't exist
        """
        try:
            if os.path.exists(self.log_file_path):
                return os.path.getsize(self.log_file_path)
            return 0
        except Exception:
            return 0

    def get_log_stats(self) -> Dict[str, any]:
        """
        Get statistics about security logging.

        Returns:
            Dict with log file stats:
            {
                "log_file_path": str,
                "file_size_bytes": int,
                "file_size_mb": float,
                "backup_count": int,
                "max_size_mb": int
            }
        """
        file_size = self.get_log_file_size()

        # Count backup files (security.log.1, security.log.2, ...)
        log_dir = os.path.dirname(self.log_file_path)
        backup_count = 0
        for i in range(1, 11):
            backup_path = f"{self.log_file_path}.{i}"
            if os.path.exists(backup_path):
                backup_count += 1

        return {
            "log_file_path": self.log_file_path,
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "backup_count": backup_count,
            "max_size_mb": 10,
            "max_backups": 10
        }


# Singleton instance for global access
_security_logger_instance = None


def get_security_logger(log_dir: str = None) -> SecurityLogger:
    """
    Get or create the global SecurityLogger instance.

    Args:
        log_dir: Optional log directory (only used on first call)

    Returns:
        SecurityLogger instance
    """
    global _security_logger_instance
    if _security_logger_instance is None:
        _security_logger_instance = SecurityLogger(log_dir=log_dir)
    return _security_logger_instance
