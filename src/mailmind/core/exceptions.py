"""
Custom exception hierarchy for MailMind application.

All exceptions inherit from MailMindException base class and include:
- user_message: User-friendly error message (AC5 - avoid technical jargon)
- technical_details: Technical error details for logging (AC4)

Story 2.6 AC1: Graceful Error Handling
Story 2.6 AC5: User-Friendly Error Messages
"""

from typing import Optional


class MailMindException(Exception):
    """
    Base exception class for all MailMind errors.

    All custom exceptions inherit from this class and provide:
    - user_message: User-friendly error message for display
    - technical_details: Technical details for logging and debugging
    """

    def __init__(
        self,
        user_message: str,
        technical_details: Optional[str] = None,
        *args, **kwargs
    ):
        """
        Initialize MailMindException.

        Args:
            user_message: User-friendly error message (no technical jargon)
            technical_details: Technical details for logging (optional)
        """
        super().__init__(user_message, *args, **kwargs)
        self.user_message = user_message
        self.technical_details = technical_details or user_message

    def __str__(self) -> str:
        """Return user-friendly message."""
        return self.user_message


# ============================================================================
# Ollama-related exceptions (Story 1.1 integration)
# ============================================================================

class OllamaError(MailMindException):
    """Base exception for Ollama-related errors."""
    pass


class OllamaConnectionError(OllamaError):
    """
    Raised when Ollama service is not available or not installed.

    AC12: Error Scenario - Ollama not installed
    """

    def __init__(self, technical_details: Optional[str] = None):
        user_message = (
            "MailMind requires Ollama to run AI features. "
            "Please download Ollama from https://ollama.ai/download and restart the application."
        )
        super().__init__(user_message, technical_details)


class OllamaModelError(OllamaError):
    """
    Raised when required AI model is not available.

    AC12: Error Scenario - Model not downloaded
    AC3: Model Fallback - triggers fallback to Mistral
    """

    def __init__(self, model_name: str, technical_details: Optional[str] = None):
        user_message = (
            f"AI model '{model_name}' is not available. "
            f"Downloading model (this may take 10-20 minutes)... "
            f"Alternatively, you can manually run: ollama pull {model_name}"
        )
        super().__init__(user_message, technical_details or f"Model not found: {model_name}")
        self.model_name = model_name


# ============================================================================
# Outlook-related exceptions (Story 2.1 integration)
# ============================================================================

class OutlookError(MailMindException):
    """Base exception for Outlook-related errors."""

    def __init__(
        self,
        user_message: str,
        technical_details: Optional[str] = None,
        error_code: Optional[int] = None
    ):
        super().__init__(user_message, technical_details)
        self.error_code = error_code


class OutlookNotInstalledException(OutlookError):
    """
    Raised when Microsoft Outlook is not installed.

    AC12: Error Scenario - Outlook not installed
    """

    def __init__(self, technical_details: Optional[str] = None):
        user_message = (
            "Microsoft Outlook is not installed on this system. "
            "MailMind requires Outlook 2016 or later to access your emails."
        )
        super().__init__(user_message, technical_details)


class OutlookNotRunningException(OutlookError):
    """
    Raised when Microsoft Outlook is not running.

    AC12: Error Scenario - Outlook not running
    AC2: Automatic Recovery - triggers retry logic
    """

    def __init__(self, technical_details: Optional[str] = None):
        user_message = (
            "Microsoft Outlook is not running. "
            "Please start Outlook and try again."
        )
        super().__init__(user_message, technical_details)


class OutlookConnectionError(OutlookError):
    """
    Raised when connection to Outlook fails.

    AC2: Automatic Recovery - triggers retry logic with exponential backoff
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[int] = None,
        technical_details: Optional[str] = None
    ):
        user_message = (
            f"Failed to connect to Outlook. {message} "
            f"Please ensure Outlook is running and try again."
        )
        super().__init__(user_message, technical_details or message, error_code)


class OutlookProfileNotConfiguredException(OutlookError):
    """Raised when Outlook profile is not configured."""

    def __init__(self, technical_details: Optional[str] = None):
        user_message = (
            "Outlook email profile is not configured. "
            "Please configure an email account in Outlook and try again."
        )
        super().__init__(user_message, technical_details)


class OutlookPermissionDeniedException(OutlookError):
    """Raised when Outlook denies permission."""

    def __init__(self, technical_details: Optional[str] = None):
        user_message = (
            "Outlook denied permission to access emails. "
            "Please grant permission when prompted by Outlook security dialog."
        )
        super().__init__(user_message, technical_details)


class OutlookFolderNotFoundException(OutlookError):
    """Raised when Outlook folder is not found."""

    def __init__(self, folder_name: str, technical_details: Optional[str] = None):
        user_message = (
            f"Email folder '{folder_name}' was not found. "
            f"Please check the folder name and try again."
        )
        super().__init__(user_message, technical_details or f"Folder not found: {folder_name}")
        self.folder_name = folder_name


class OutlookEmailNotFoundException(OutlookError):
    """Raised when email is not found."""

    def __init__(self, email_id: str, technical_details: Optional[str] = None):
        user_message = (
            "The requested email was not found. "
            "It may have been moved or deleted."
        )
        super().__init__(user_message, technical_details or f"Email not found: {email_id}")
        self.email_id = email_id


# ============================================================================
# Database-related exceptions (Story 2.2 integration)
# ============================================================================

class DatabaseError(MailMindException):
    """Base exception for database-related errors."""
    pass


class DatabaseCorruptionError(DatabaseError):
    """
    Raised when database corruption is detected.

    AC12: Error Scenario - Database corruption
    Triggers automatic backup restoration
    """

    def __init__(self, technical_details: Optional[str] = None):
        user_message = (
            "Database corruption detected. "
            "Attempting to restore from backup... This may take a few moments."
        )
        super().__init__(user_message, technical_details)


class DatabaseBackupError(DatabaseError):
    """Raised when database backup or restore fails."""

    def __init__(self, operation: str, technical_details: Optional[str] = None):
        user_message = (
            f"Database {operation} failed. "
            f"Please check disk space and file permissions."
        )
        super().__init__(user_message, technical_details or f"{operation} failed")
        self.operation = operation


# ============================================================================
# System-related exceptions
# ============================================================================

class SystemError(MailMindException):
    """Base exception for system-related errors."""
    pass


class InsufficientMemoryError(SystemError):
    """
    Raised when available memory is insufficient.

    AC12: Error Scenario - Insufficient memory
    AC6: Graceful degradation - triggers memory optimization
    """

    def __init__(self, available_gb: float, required_gb: float, technical_details: Optional[str] = None):
        user_message = (
            f"Insufficient memory detected ({available_gb:.1f}GB available, {required_gb:.1f}GB recommended). "
            f"For better performance, please close some applications. "
            f"MailMind will continue with reduced performance."
        )
        super().__init__(
            user_message,
            technical_details or f"Memory: {available_gb:.1f}GB available, {required_gb:.1f}GB required"
        )
        self.available_gb = available_gb
        self.required_gb = required_gb


class DiskSpaceError(SystemError):
    """Raised when insufficient disk space is available."""

    def __init__(self, available_gb: float, required_gb: float, technical_details: Optional[str] = None):
        user_message = (
            f"Insufficient disk space ({available_gb:.1f}GB available, {required_gb:.1f}GB required). "
            f"Please free up disk space and try again."
        )
        super().__init__(
            user_message,
            technical_details or f"Disk space: {available_gb:.1f}GB available, {required_gb:.1f}GB required"
        )
        self.available_gb = available_gb
        self.required_gb = required_gb


# ============================================================================
# Configuration exceptions
# ============================================================================

class ConfigurationError(MailMindException):
    """Base exception for configuration-related errors."""
    pass


class InvalidSettingError(ConfigurationError):
    """Raised when a setting has an invalid value."""

    def __init__(self, setting_name: str, value: any, reason: str):
        user_message = (
            f"Invalid setting '{setting_name}': {reason}. "
            f"Please check your configuration."
        )
        super().__init__(
            user_message,
            f"Invalid setting: {setting_name}={value}, reason: {reason}"
        )
        self.setting_name = setting_name
        self.value = value
        self.reason = reason


# ============================================================================
# Update system exceptions
# ============================================================================

class UpdateError(MailMindException):
    """Base exception for update-related errors."""
    pass


class UpdateDownloadError(UpdateError):
    """Raised when update download fails."""

    def __init__(self, version: str, technical_details: Optional[str] = None):
        user_message = (
            f"Failed to download update version {version}. "
            f"Please check your internet connection and try again later."
        )
        super().__init__(user_message, technical_details or f"Download failed: v{version}")
        self.version = version


class UpdateVerificationError(UpdateError):
    """Raised when update verification fails."""

    def __init__(self, technical_details: Optional[str] = None):
        user_message = (
            "Update package verification failed. "
            "The downloaded file may be corrupted. Please try downloading again."
        )
        super().__init__(user_message, technical_details)


class UpdateInstallationError(UpdateError):
    """Raised when update installation fails."""

    def __init__(self, technical_details: Optional[str] = None):
        user_message = (
            "Update installation failed. "
            "Rolling back to previous version..."
        )
        super().__init__(user_message, technical_details)


# ============================================================================
# Email Preprocessing exceptions (Story 1.2, Story 3.2)
# ============================================================================

class EmailPreprocessorError(MailMindException):
    """Base exception for email preprocessing errors."""
    pass


class HTMLParsingError(EmailPreprocessorError):
    """Raised when HTML parsing fails."""

    def __init__(self, technical_details: Optional[str] = None):
        user_message = (
            "Failed to parse email HTML content. "
            "The email may be displayed in simplified format."
        )
        super().__init__(user_message, technical_details)


class SecurityException(EmailPreprocessorError):
    """
    Raised when email is blocked for security reasons.

    This exception is thrown when the EmailPreprocessor detects suspicious
    content that could be a prompt injection attack or other security threat.

    Story 3.2 AC1: Block Injection Patterns
    Story 3.2 AC2: Safe Error Response

    Attributes:
        pattern_name: Name of the security pattern that triggered the block
        severity: Severity level of the matched pattern ("high", "medium", "low")
        email_preview: Optional preview of the blocked email content (first 200 chars)

    Usage:
        try:
            preprocessed = preprocessor.preprocess_email(raw_email)
        except SecurityException as e:
            logger.error(f"Email blocked: {e.pattern_name} (severity: {e.severity})")
            return {"status": "blocked", "reason": str(e)}
    """

    def __init__(self,
                 pattern_name: str,
                 severity: str = "high",
                 email_preview: str = None,
                 technical_details: Optional[str] = None):
        """
        Initialize SecurityException.

        Args:
            pattern_name: Name of the pattern that triggered the block
            severity: Severity level ("high", "medium", "low")
            email_preview: Optional preview of blocked content
            technical_details: Technical details for logging
        """
        # User-friendly message (AC2: Safe Error Response)
        user_message = (
            f"Email blocked for security reasons. "
            f"This email contains content that may be harmful. "
            f"Check Security settings to adjust protection levels."
        )

        super().__init__(
            user_message,
            technical_details or f"Pattern matched: {pattern_name} (severity: {severity})"
        )

        self.pattern_name = pattern_name
        self.severity = severity
        self.email_preview = email_preview

    def get_user_message(self) -> str:
        """
        Get a safe, user-friendly error message for display.

        Returns:
            User-friendly message without technical details
        """
        if self.pattern_name:
            return f"Email blocked: {self.pattern_name.replace('_', ' ').title()}"
        return "Email blocked for security reasons"
