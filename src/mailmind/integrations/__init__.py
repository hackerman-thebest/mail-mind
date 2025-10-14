"""
Outlook Integration Module for MailMind.

This module provides COM-based integration with Microsoft Outlook,
enabling email fetching, management, and synchronization.

Main Components:
- OutlookConnector: Main interface for Outlook COM operations
- OutlookEmail: Type-safe email data model
- Custom exceptions: Domain-specific error handling

Example:
    from mailmind.integrations import OutlookConnector, OutlookNotInstalledError

    connector = OutlookConnector()
    try:
        if connector.connect():
            print("Connected to Outlook!")
    except OutlookNotInstalledError:
        print("Please install Microsoft Outlook")
"""

from .outlook_connector import OutlookConnector
from .outlook_models import (
    OutlookEmail,
    OutlookAccount,
    OutlookFolder,
    OutlookAttachment,
    ConnectionStatus,
    ConnectionState,
    EmailImportance,
    FlagStatus,
)
from .outlook_errors import (
    OutlookError,
    OutlookNotInstalledException,
    OutlookNotRunningException,
    OutlookConnectionError,
    OutlookProfileNotConfiguredException,
    OutlookPermissionDeniedException,
    OutlookFolderNotFoundException,
    OutlookEmailNotFoundException,
    OutlookActionFailedException,
)

__all__ = [
    # Main connector
    'OutlookConnector',
    # Data models
    'OutlookEmail',
    'OutlookAccount',
    'OutlookFolder',
    'OutlookAttachment',
    'ConnectionStatus',
    'ConnectionState',
    'EmailImportance',
    'FlagStatus',
    # Exceptions
    'OutlookError',
    'OutlookNotInstalledException',
    'OutlookNotRunningException',
    'OutlookConnectionError',
    'OutlookProfileNotConfiguredException',
    'OutlookPermissionDeniedException',
    'OutlookFolderNotFoundException',
    'OutlookEmailNotFoundException',
    'OutlookActionFailedException',
]
