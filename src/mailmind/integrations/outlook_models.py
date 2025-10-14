"""
Data models for Outlook integration.

This module defines dataclasses for type-safe storage of Outlook objects,
providing a clean interface between Outlook COM objects and MailMind's
internal representation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class ConnectionStatus(Enum):
    """Outlook connection status."""
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    DISCONNECTED = "disconnected"


class EmailImportance(Enum):
    """Outlook email importance level."""
    LOW = 0
    NORMAL = 1
    HIGH = 2


class FlagStatus(Enum):
    """Outlook email flag status."""
    NOT_FLAGGED = 0
    FLAGGED = 2
    COMPLETED = 1


@dataclass
class OutlookAccount:
    """Represents an Outlook email account."""

    email_address: str
    display_name: str
    account_type: str  # Exchange, IMAP, POP3, etc.
    smtp_address: Optional[str] = None

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.display_name} <{self.email_address}>"


@dataclass
class OutlookFolder:
    """Represents an Outlook folder."""

    name: str
    entry_id: str
    folder_path: str
    item_count: int
    unread_count: int
    parent_folder: Optional[str] = None

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.folder_path} ({self.unread_count}/{self.item_count} unread)"


@dataclass
class OutlookAttachment:
    """Represents an email attachment."""

    filename: str
    size: int  # Size in bytes
    content_type: Optional[str] = None

    def __str__(self) -> str:
        """Return string representation."""
        size_kb = self.size / 1024
        return f"{self.filename} ({size_kb:.1f} KB)"


@dataclass
class OutlookEmail:
    """
    Represents an Outlook email with all relevant properties.

    This dataclass provides type-safe storage for email properties extracted
    from Outlook MailItem COM objects.
    """

    # Required properties
    entry_id: str  # Unique identifier
    subject: str
    sender_email: str
    sender_name: str
    received_time: datetime

    # Body content
    body: str = ""
    body_html: str = ""

    # Thread information
    conversation_id: Optional[str] = None
    conversation_topic: Optional[str] = None
    in_reply_to: Optional[str] = None

    # Email metadata
    message_class: str = "IPM.Note"
    importance: EmailImportance = EmailImportance.NORMAL
    flag_status: FlagStatus = FlagStatus.NOT_FLAGGED
    is_unread: bool = True

    # Recipients
    to_recipients: List[str] = field(default_factory=list)
    cc_recipients: List[str] = field(default_factory=list)
    bcc_recipients: List[str] = field(default_factory=list)

    # Attachments
    attachments: List[OutlookAttachment] = field(default_factory=list)
    has_attachments: bool = False

    # Folder information
    folder_name: Optional[str] = None

    # Timestamps
    creation_time: Optional[datetime] = None
    last_modification_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert email to dictionary format for integration with EmailPreprocessor.

        Returns:
            Dictionary with keys compatible with EmailPreprocessor.preprocess_email()
        """
        return {
            'from': f"{self.sender_email} ({self.sender_name})",
            'subject': self.subject,
            'body': self.body,
            'body_html': self.body_html,
            'date': self.received_time.isoformat(),
            'message_id': self.entry_id,
            'to': ', '.join(self.to_recipients) if self.to_recipients else '',
            'cc': ', '.join(self.cc_recipients) if self.cc_recipients else '',
            'attachments': [
                {
                    'filename': att.filename,
                    'size': att.size,
                    'content_type': att.content_type
                }
                for att in self.attachments
            ],
            'thread_info': {
                'conversation_id': self.conversation_id,
                'conversation_topic': self.conversation_topic,
                'in_reply_to': self.in_reply_to
            }
        }

    def __str__(self) -> str:
        """Return string representation."""
        status = "unread" if self.is_unread else "read"
        return f"[{status}] {self.subject} from {self.sender_name} ({self.received_time.strftime('%Y-%m-%d %H:%M')})"


@dataclass
class ConnectionState:
    """Represents the current connection state to Outlook."""

    status: ConnectionStatus
    last_connected: Optional[datetime] = None
    last_error: Optional[str] = None
    retry_count: int = 0

    def is_connected(self) -> bool:
        """Check if currently connected."""
        return self.status == ConnectionStatus.CONNECTED

    def __str__(self) -> str:
        """Return string representation."""
        if self.status == ConnectionStatus.CONNECTED and self.last_connected:
            return f"Connected (since {self.last_connected.strftime('%H:%M:%S')})"
        elif self.status == ConnectionStatus.RECONNECTING:
            return f"Reconnecting (attempt {self.retry_count})"
        else:
            return "Disconnected"
