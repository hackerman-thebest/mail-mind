"""
Custom exceptions for Outlook integration.

This module defines domain-specific exceptions for Outlook COM operations,
providing clear error messages and actionable feedback for users.
"""


class OutlookError(Exception):
    """Base exception for all Outlook-related errors."""

    def __init__(self, message: str, error_code: int = None, details: str = None):
        """
        Initialize OutlookError.

        Args:
            message: User-friendly error message
            error_code: COM error code (if applicable)
            details: Additional technical details for debugging
        """
        self.message = message
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return formatted error message."""
        msg = self.message
        if self.error_code:
            msg += f" (Error Code: {self.error_code})"
        if self.details:
            msg += f"\nDetails: {self.details}"
        return msg


class OutlookNotInstalledException(OutlookError):
    """Raised when Outlook is not installed on the system."""

    def __init__(self, details: str = None):
        super().__init__(
            message=(
                "Microsoft Outlook is not installed on this system. "
                "MailMind requires Outlook to be installed to access your emails. "
                "Please install Microsoft Outlook and try again."
            ),
            error_code=-2147221005,
            details=details
        )


class OutlookNotRunningException(OutlookError):
    """Raised when Outlook is installed but not running."""

    def __init__(self, details: str = None):
        super().__init__(
            message=(
                "Microsoft Outlook is not currently running. "
                "Please start Outlook and try connecting again."
            ),
            error_code=-2147023174,
            details=details
        )


class OutlookConnectionError(OutlookError):
    """Raised when connection to Outlook fails for any reason."""

    def __init__(self, message: str = None, error_code: int = None, details: str = None):
        if message is None:
            message = "Failed to connect to Microsoft Outlook. Please ensure Outlook is running and try again."
        super().__init__(message=message, error_code=error_code, details=details)


class OutlookProfileNotConfiguredException(OutlookError):
    """Raised when Outlook is running but no email profile is configured."""

    def __init__(self, details: str = None):
        super().__init__(
            message=(
                "No Outlook email profile is configured. "
                "Please configure at least one email account in Outlook and try again."
            ),
            details=details
        )


class OutlookPermissionDeniedException(OutlookError):
    """Raised when permission is denied to access Outlook."""

    def __init__(self, details: str = None):
        super().__init__(
            message=(
                "Permission denied to access Outlook. "
                "Please grant the necessary permissions and try again."
            ),
            error_code=-2147024891,
            details=details
        )


class OutlookFolderNotFoundException(OutlookError):
    """Raised when a requested folder is not found."""

    def __init__(self, folder_name: str, details: str = None):
        super().__init__(
            message=f"Folder '{folder_name}' not found in Outlook.",
            details=details
        )


class OutlookEmailNotFoundException(OutlookError):
    """Raised when a requested email is not found."""

    def __init__(self, email_id: str, details: str = None):
        super().__init__(
            message=f"Email with ID '{email_id}' not found.",
            details=details
        )


class OutlookActionFailedException(OutlookError):
    """Raised when an Outlook action (move, delete, etc.) fails."""

    def __init__(self, action: str, reason: str = None, details: str = None):
        message = f"Failed to {action}"
        if reason:
            message += f": {reason}"
        super().__init__(message=message, details=details)
