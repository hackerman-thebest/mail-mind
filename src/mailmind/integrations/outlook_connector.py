"""
Outlook COM interface connector for MailMind.

This module provides the OutlookConnector class, which acts as an adapter
between MailMind's internal email representation and Outlook's COM interface
using pywin32. It isolates all pywin32 dependencies to enable easier migration
to Microsoft Graph API in v2.0.

Design Pattern: Adapter Pattern
- Wraps Outlook COM objects in type-safe dataclasses
- Translates COM errors to domain-specific exceptions
- Provides retry logic for transient failures
"""

import logging
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any
import time

# Import Windows-specific dependencies conditionally for cross-platform testing
_WINDOWS_AVAILABLE = sys.platform == 'win32'

if _WINDOWS_AVAILABLE:
    try:
        import win32com.client
        import pywintypes
        import psutil
    except ImportError as e:
        raise ImportError(
            f"Required dependencies not installed: {e}. "
            "Please install: pip install pywin32 psutil"
        )
else:
    # For testing on non-Windows platforms, use mock objects
    win32com = None
    pywintypes = None
    try:
        import psutil
    except ImportError:
        psutil = None

from .outlook_errors import (
    OutlookError,
    OutlookNotInstalledException,
    OutlookNotRunningException,
    OutlookConnectionError,
    OutlookProfileNotConfiguredException,
    OutlookPermissionDeniedException,
    OutlookFolderNotFoundException,
    OutlookEmailNotFoundException,
)
from .outlook_models import (
    ConnectionStatus,
    ConnectionState,
    OutlookEmail,
    OutlookFolder,
    OutlookAttachment,
    EmailImportance,
    FlagStatus,
)

# Import retry decorator for automatic reconnection (Story 2.6 AC2)
try:
    from mailmind.core.error_handler import retry
except ImportError:
    # Fallback: Define a no-op decorator if error_handler not available yet
    def retry(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

logger = logging.getLogger(__name__)


class OutlookConnector:
    """
    Main connector class for Outlook COM interface.

    This class provides connection management, error handling, and basic
    operations for interacting with Microsoft Outlook via COM automation.

    Example:
        connector = OutlookConnector()
        if connector.connect():
            print(f"Connected! Status: {connector.connection_state}")
        else:
            print(f"Connection failed: {connector.connection_state.last_error}")
    """

    def __init__(self):
        """Initialize OutlookConnector."""
        if not _WINDOWS_AVAILABLE:
            logger.warning("OutlookConnector is only available on Windows (running on non-Windows for testing)")

        self._outlook_app: Optional[Any] = None
        self._namespace: Optional[Any] = None
        self._connection_state = ConnectionState(status=ConnectionStatus.DISCONNECTED)
        self._folder_cache: Dict[str, Any] = {}  # Cache folders to minimize COM calls
        logger.info("OutlookConnector initialized")

    @property
    def connection_state(self) -> ConnectionState:
        """
        Get current connection state.

        Returns:
            ConnectionState object with status and metadata
        """
        return self._connection_state

    @property
    def is_connected(self) -> bool:
        """
        Check if currently connected to Outlook.

        Returns:
            True if connected, False otherwise
        """
        return self._connection_state.is_connected()

    @staticmethod
    def detect_outlook_installed() -> bool:
        """
        Detect if Microsoft Outlook is installed on the system.

        This method checks for Outlook installation by attempting to query
        the COM registration. It does not require Outlook to be running.

        Returns:
            True if Outlook is installed, False otherwise

        Example:
            if OutlookConnector.detect_outlook_installed():
                print("Outlook is installed")
            else:
                print("Outlook is not installed")
        """
        try:
            # Try to get the Outlook COM object type without dispatching
            import winreg

            # Check HKEY_CLASSES_ROOT for Outlook.Application
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CLASSES_ROOT,
                    "Outlook.Application",
                    0,
                    winreg.KEY_READ
                )
                winreg.CloseKey(key)
                logger.info("Outlook installation detected via registry")
                return True
            except FileNotFoundError:
                logger.warning("Outlook.Application not found in registry")
                return False
            except Exception as e:
                logger.warning(f"Error checking registry: {e}")

                # Fallback: Try to dispatch without connecting
                try:
                    # This will fail if Outlook is not installed
                    win32com.client.Dispatch("Outlook.Application")
                    logger.info("Outlook installation detected via COM dispatch")
                    return True
                except pywintypes.com_error as com_err:
                    error_code = com_err.args[0] if com_err.args else None
                    if error_code == -2147221005:  # Class not registered
                        logger.warning("Outlook COM class not registered")
                        return False
                    # Other errors might mean Outlook is installed but not running
                    logger.info(f"Outlook may be installed (COM error: {error_code})")
                    return True
                except Exception as dispatch_err:
                    logger.error(f"Unexpected error during dispatch check: {dispatch_err}")
                    return False

        except Exception as e:
            logger.error(f"Error detecting Outlook installation: {e}")
            return False

    @staticmethod
    def is_outlook_running() -> bool:
        """
        Detect if Microsoft Outlook is currently running.

        This method checks the running processes to determine if OUTLOOK.EXE
        is active. It does not verify connection health.

        Returns:
            True if Outlook process is running, False otherwise

        Example:
            if OutlookConnector.is_outlook_running():
                print("Outlook is running")
            else:
                print("Please start Outlook")
        """
        try:
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'].lower() == 'outlook.exe':
                        logger.debug("Outlook.exe process found")
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            logger.debug("Outlook.exe process not found")
            return False
        except Exception as e:
            logger.error(f"Error checking if Outlook is running: {e}")
            return False

    @retry(
        max_retries=5,
        initial_delay=1.0,
        backoff_multiplier=2.0,
        max_delay=16.0,
        exceptions=(OutlookNotRunningException, OutlookConnectionError)
    )
    def connect(self) -> bool:
        """
        Establish connection to Microsoft Outlook with automatic retry logic.

        This method attempts to connect to Outlook via COM automation with exponential
        backoff retry (1s → 2s → 4s → 8s → 16s, max 5 retries). It performs
        the following checks:
        1. Verify Outlook is installed
        2. Verify Outlook is running
        3. Dispatch to Outlook.Application
        4. Access MAPI namespace
        5. Verify at least one account is configured

        Story 2.6 AC2: Automatic recovery from Outlook disconnection with retry logic

        Returns:
            True if connection successful, False otherwise

        Raises:
            OutlookNotInstalledException: If Outlook is not installed (no retry)
            OutlookNotRunningException: If Outlook is not running (retries automatically)
            OutlookProfileNotConfiguredException: If no email profile exists (no retry)
            OutlookConnectionError: For other connection failures (retries automatically)

        Example:
            connector = OutlookConnector()
            try:
                if connector.connect():
                    print("Connected successfully!")
            except OutlookNotInstalledException:
                print("Please install Outlook")
            except OutlookNotRunningException:
                print("Please start Outlook")
        """
        logger.info("Attempting to connect to Outlook...")

        # Step 1: Check if Outlook is installed
        if not self.detect_outlook_installed():
            error_msg = "Outlook is not installed on this system"
            logger.error(error_msg)
            self._connection_state.last_error = error_msg
            raise OutlookNotInstalledException(
                details="Registry check failed for Outlook.Application"
            )

        # Step 2: Check if Outlook is running
        if not self.is_outlook_running():
            error_msg = "Outlook is not running"
            logger.error(error_msg)
            self._connection_state.last_error = error_msg
            raise OutlookNotRunningException(
                details="OUTLOOK.EXE process not found"
            )

        # Step 3: Attempt COM connection
        try:
            logger.debug("Dispatching to Outlook.Application...")
            self._outlook_app = win32com.client.Dispatch("Outlook.Application")

            # Step 4: Get MAPI namespace
            logger.debug("Getting MAPI namespace...")
            self._namespace = self._outlook_app.GetNamespace("MAPI")

            # Step 5: Verify accounts are configured
            try:
                accounts = self._namespace.Accounts
                if accounts.Count == 0:
                    error_msg = "No email accounts configured in Outlook"
                    logger.error(error_msg)
                    self._connection_state.last_error = error_msg
                    raise OutlookProfileNotConfiguredException(
                        details="Accounts.Count = 0"
                    )

                logger.info(f"Found {accounts.Count} configured account(s)")
            except OutlookProfileNotConfiguredException:
                # Re-raise profile exception - this is a critical error
                raise
            except Exception as account_err:
                logger.warning(f"Could not verify accounts: {account_err}")
                # Continue anyway - some Outlook versions may not support this check

            # Step 6: Update connection state
            self._connection_state.status = ConnectionStatus.CONNECTED
            self._connection_state.last_connected = datetime.now()
            self._connection_state.last_error = None
            self._connection_state.retry_count = 0

            logger.info("✅ Successfully connected to Outlook")
            return True

        except (OutlookNotInstalledException, OutlookNotRunningException,
                OutlookProfileNotConfiguredException, OutlookPermissionDeniedException):
            # Re-raise our custom exceptions without modification
            raise

        except Exception as e:
            # Check if it's a COM error (only on Windows with pywintypes)
            if pywintypes and hasattr(pywintypes, 'com_error') and isinstance(e, pywintypes.com_error):
                error_code = e.args[0] if e.args else None
                error_msg = str(e)

                logger.error(f"COM error during connection: {error_code} - {error_msg}")
                self._connection_state.last_error = error_msg

                # Map known COM error codes
                if error_code == -2147221005:  # REGDB_E_CLASSNOTREG
                    raise OutlookNotInstalledException(
                        details=f"COM error {error_code}: {error_msg}"
                    )
                elif error_code == -2147023174:  # RPC_S_SERVER_UNAVAILABLE
                    raise OutlookNotRunningException(
                        details=f"COM error {error_code}: {error_msg}"
                    )
                elif error_code == -2147024891:  # E_ACCESSDENIED
                    raise OutlookPermissionDeniedException(
                        details=f"COM error {error_code}: {error_msg}"
                    )
                else:
                    raise OutlookConnectionError(
                        message=f"Failed to connect to Outlook (COM error {error_code})",
                        error_code=error_code,
                        details=error_msg
                    )

            # Not a COM error - handle as generic exception
            error_msg = f"Unexpected error during connection: {e}"
            logger.error(error_msg, exc_info=True)
            self._connection_state.last_error = error_msg
            raise OutlookConnectionError(
                message="An unexpected error occurred while connecting to Outlook",
                details=error_msg
            )

    def get_folder(self, folder_name: str = "Inbox") -> Any:
        """
        Get an Outlook folder by name.

        This method retrieves a folder object and caches it for future use
        to minimize COM calls.

        Args:
            folder_name: Name of the folder (default: "Inbox")
                       Common folders: "Inbox", "Sent Items", "Drafts", "Deleted Items"

        Returns:
            Outlook folder object

        Raises:
            OutlookConnectionError: If not connected
            OutlookFolderNotFoundException: If folder not found

        Example:
            connector = OutlookConnector()
            connector.connect()
            inbox = connector.get_folder("Inbox")
            sent = connector.get_folder("Sent Items")
        """
        if not self.is_connected:
            raise OutlookConnectionError("Not connected to Outlook")

        # Check cache first
        if folder_name in self._folder_cache:
            logger.debug(f"Retrieved folder '{folder_name}' from cache")
            return self._folder_cache[folder_name]

        try:
            # Map common folder names to Outlook constants
            folder_map = {
                "Inbox": 6,           # olFolderInbox
                "Sent Items": 5,      # olFolderSentMail
                "Drafts": 16,         # olFolderDrafts
                "Deleted Items": 3,   # olFolderDeletedItems
                "Outbox": 4,          # olFolderOutbox
                "Junk Email": 23,     # olFolderJunk
            }

            if folder_name in folder_map:
                # Use GetDefaultFolder for standard folders
                folder = self._namespace.GetDefaultFolder(folder_map[folder_name])
                logger.info(f"Retrieved standard folder: {folder_name}")
            else:
                # Search for custom folder
                folders = self._namespace.Folders
                folder = None
                for folder_item in folders:
                    if folder_item.Name.lower() == folder_name.lower():
                        folder = folder_item
                        break

                if folder is None:
                    raise OutlookFolderNotFoundException(
                        folder_name=folder_name,
                        details=f"Folder '{folder_name}' not found in Outlook"
                    )

                logger.info(f"Retrieved custom folder: {folder_name}")

            # Cache the folder
            self._folder_cache[folder_name] = folder
            return folder

        except OutlookFolderNotFoundException:
            raise
        except Exception as e:
            error_msg = f"Error retrieving folder '{folder_name}': {e}"
            logger.error(error_msg)
            raise OutlookConnectionError(
                message=f"Failed to retrieve folder '{folder_name}'",
                details=error_msg
            )

    def fetch_emails(
        self,
        folder_name: str = "Inbox",
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "[ReceivedTime]",
        sort_descending: bool = True
    ) -> List['OutlookEmail']:
        """
        Fetch emails from a folder with pagination support.

        This method retrieves emails efficiently using pagination to avoid
        performance issues with large folders.

        Args:
            folder_name: Name of the folder to fetch from (default: "Inbox")
            limit: Maximum number of emails to fetch (default: 50, max: 100)
            offset: Number of emails to skip (for pagination, default: 0)
            sort_by: Property to sort by (default: "[ReceivedTime]")
            sort_descending: Sort in descending order (default: True)

        Returns:
            List of OutlookEmail objects

        Raises:
            OutlookConnectionError: If not connected
            OutlookFolderNotFoundException: If folder not found

        Example:
            connector = OutlookConnector()
            connector.connect()

            # Fetch first 50 emails
            emails = connector.fetch_emails("Inbox", limit=50, offset=0)

            # Fetch next 50 emails
            more_emails = connector.fetch_emails("Inbox", limit=50, offset=50)

            for email in emails:
                print(f"{email.subject} from {email.sender_name}")
        """
        if not self.is_connected:
            raise OutlookConnectionError("Not connected to Outlook")

        # Enforce max limit
        if limit > 100:
            logger.warning(f"Limit {limit} exceeds max 100, capping at 100")
            limit = 100

        try:
            # Get the folder
            folder = self.get_folder(folder_name)

            # Get items collection
            items = folder.Items

            # Sort items
            items.Sort(sort_by, sort_descending)

            # Get total count
            total_count = items.Count
            logger.info(f"Folder '{folder_name}' contains {total_count} emails")

            # Calculate actual limit based on offset
            end_index = min(offset + limit, total_count)
            actual_limit = end_index - offset

            if actual_limit <= 0:
                logger.info(f"Offset {offset} beyond total count {total_count}, returning empty list")
                return []

            # Fetch emails (COM indexing starts at 1)
            emails: List[OutlookEmail] = []
            start_time = time.time()

            for i in range(offset, end_index):
                try:
                    mail_item = items.Item(i + 1)  # COM uses 1-based indexing

                    # Extract properties and create OutlookEmail
                    email = self._extract_email_properties(mail_item)
                    emails.append(email)

                except Exception as item_err:
                    logger.warning(f"Error fetching email at index {i}: {item_err}")
                    continue

            elapsed = time.time() - start_time
            logger.info(f"Fetched {len(emails)} emails from '{folder_name}' in {elapsed:.2f}s")

            # Performance warning for large fetches
            if elapsed > 2.0:
                logger.warning(
                    f"Fetch operation took {elapsed:.2f}s (target: <2s). "
                    f"Consider reducing limit or implementing caching."
                )

            return emails

        except OutlookFolderNotFoundException:
            raise
        except OutlookConnectionError:
            raise
        except Exception as e:
            error_msg = f"Error fetching emails from '{folder_name}': {e}"
            logger.error(error_msg, exc_info=True)
            raise OutlookConnectionError(
                message=f"Failed to fetch emails from '{folder_name}'",
                details=error_msg
            )

    def _extract_email_properties(self, mail_item: Any) -> 'OutlookEmail':
        """
        Extract properties from an Outlook MailItem and create OutlookEmail object.

        This is an internal helper method for converting COM objects to
        type-safe dataclasses.

        Args:
            mail_item: Outlook MailItem COM object

        Returns:
            OutlookEmail object with extracted properties

        Note:
            This method uses null-safe property access to handle missing properties.
        """
        try:
            # Extract required properties
            entry_id = getattr(mail_item, 'EntryID', '')
            subject = getattr(mail_item, 'Subject', '(No Subject)')
            sender_email = getattr(mail_item, 'SenderEmailAddress', '')
            sender_name = getattr(mail_item, 'SenderName', '')
            received_time = getattr(mail_item, 'ReceivedTime', datetime.now())

            # Convert COM datetime to Python datetime if needed
            if not isinstance(received_time, datetime):
                try:
                    received_time = datetime(
                        received_time.year,
                        received_time.month,
                        received_time.day,
                        received_time.hour,
                        received_time.minute,
                        received_time.second
                    )
                except:
                    received_time = datetime.now()

            # Extract body content
            body = getattr(mail_item, 'Body', '')
            body_html = getattr(mail_item, 'HTMLBody', '')

            # Extract thread information
            conversation_id = getattr(mail_item, 'ConversationID', None)
            conversation_topic = getattr(mail_item, 'ConversationTopic', None)
            # InReplyTo may not be available in all Outlook versions
            in_reply_to = None

            # Extract metadata
            message_class = getattr(mail_item, 'MessageClass', 'IPM.Note')
            importance_value = getattr(mail_item, 'Importance', 1)  # 0=Low, 1=Normal, 2=High
            importance = EmailImportance(importance_value)

            flag_status_value = getattr(mail_item, 'FlagStatus', 0)
            flag_status = FlagStatus(flag_status_value)

            is_unread = getattr(mail_item, 'UnRead', False)

            # Extract recipients
            to_recipients = []
            try:
                recipients = mail_item.Recipients
                for recipient in recipients:
                    if recipient.Type == 1:  # olTo
                        to_recipients.append(recipient.Address)
            except:
                pass

            cc_recipients = []
            # CC recipients would need similar extraction

            # Extract attachments
            attachments = []
            has_attachments = False
            try:
                if mail_item.Attachments.Count > 0:
                    has_attachments = True
                    for attachment in mail_item.Attachments:
                        att = OutlookAttachment(
                            filename=attachment.FileName,
                            size=attachment.Size,
                            content_type=None  # Not available in COM
                        )
                        attachments.append(att)
            except:
                pass

            # Extract timestamps
            creation_time = getattr(mail_item, 'CreationTime', None)
            last_modification_time = getattr(mail_item, 'LastModificationTime', None)

            # Convert COM datetimes
            if creation_time and not isinstance(creation_time, datetime):
                try:
                    creation_time = datetime(
                        creation_time.year, creation_time.month, creation_time.day,
                        creation_time.hour, creation_time.minute, creation_time.second
                    )
                except:
                    creation_time = None

            if last_modification_time and not isinstance(last_modification_time, datetime):
                try:
                    last_modification_time = datetime(
                        last_modification_time.year, last_modification_time.month, last_modification_time.day,
                        last_modification_time.hour, last_modification_time.minute, last_modification_time.second
                    )
                except:
                    last_modification_time = None

            # Create OutlookEmail object
            return OutlookEmail(
                entry_id=entry_id,
                subject=subject,
                sender_email=sender_email,
                sender_name=sender_name,
                received_time=received_time,
                body=body,
                body_html=body_html,
                conversation_id=conversation_id,
                conversation_topic=conversation_topic,
                in_reply_to=in_reply_to,
                message_class=message_class,
                importance=importance,
                flag_status=flag_status,
                is_unread=is_unread,
                to_recipients=to_recipients,
                cc_recipients=cc_recipients,
                attachments=attachments,
                has_attachments=has_attachments,
                folder_name=None,  # Will be set by caller if needed
                creation_time=creation_time,
                last_modification_time=last_modification_time
            )

        except Exception as e:
            logger.error(f"Error extracting email properties: {e}", exc_info=True)
            # Return a minimal email object on error
            return OutlookEmail(
                entry_id=getattr(mail_item, 'EntryID', 'unknown'),
                subject=getattr(mail_item, 'Subject', '(Error extracting email)'),
                sender_email='',
                sender_name='',
                received_time=datetime.now()
            )

    def move_email(self, email_id: str, destination_folder: str) -> bool:
        """
        Move an email to a different folder.

        Args:
            email_id: EntryID of the email to move
            destination_folder: Name of the destination folder

        Returns:
            True if successful

        Raises:
            OutlookConnectionError: If not connected
            OutlookEmailNotFoundException: If email not found
            OutlookFolderNotFoundException: If destination folder not found

        Example:
            connector.move_email(email.entry_id, "Archive")
        """
        if not self.is_connected:
            raise OutlookConnectionError("Not connected to Outlook")

        try:
            # Get the email by ID
            mail_item = self._namespace.GetItemFromID(email_id)

            # Get the destination folder
            dest_folder = self.get_folder(destination_folder)

            # Move the email
            mail_item.Move(dest_folder)

            logger.info(f"Moved email '{email_id[:20]}...' to folder '{destination_folder}'")
            return True

        except OutlookFolderNotFoundException:
            raise
        except Exception as e:
            error_msg = f"Error moving email: {e}"
            logger.error(error_msg)
            if "not found" in str(e).lower():
                raise OutlookEmailNotFoundException(
                    email_id=email_id,
                    details=error_msg
                )
            raise OutlookConnectionError(
                message=f"Failed to move email",
                details=error_msg
            )

    def mark_as_read(self, email_id: str, is_read: bool = True) -> bool:
        """
        Mark an email as read or unread.

        Args:
            email_id: EntryID of the email
            is_read: True to mark as read, False to mark as unread

        Returns:
            True if successful

        Raises:
            OutlookConnectionError: If not connected
            OutlookEmailNotFoundException: If email not found

        Example:
            connector.mark_as_read(email.entry_id, is_read=True)
            connector.mark_as_read(email.entry_id, is_read=False)  # Mark as unread
        """
        if not self.is_connected:
            raise OutlookConnectionError("Not connected to Outlook")

        try:
            # Get the email by ID
            mail_item = self._namespace.GetItemFromID(email_id)

            # Set UnRead property (note: it's inverted)
            mail_item.UnRead = not is_read

            # Save changes
            mail_item.Save()

            status = "read" if is_read else "unread"
            logger.info(f"Marked email '{email_id[:20]}...' as {status}")
            return True

        except Exception as e:
            error_msg = f"Error marking email as {'read' if is_read else 'unread'}: {e}"
            logger.error(error_msg)
            if "not found" in str(e).lower():
                raise OutlookEmailNotFoundException(
                    email_id=email_id,
                    details=error_msg
                )
            raise OutlookConnectionError(
                message=f"Failed to mark email",
                details=error_msg
            )

    def create_reply_draft(self, email_id: str) -> str:
        """
        Create a reply draft for an email.

        Args:
            email_id: EntryID of the email to reply to

        Returns:
            EntryID of the created draft

        Raises:
            OutlookConnectionError: If not connected
            OutlookEmailNotFoundException: If email not found

        Example:
            draft_id = connector.create_reply_draft(email.entry_id)
            # Draft is created in Drafts folder and can be edited
        """
        if not self.is_connected:
            raise OutlookConnectionError("Not connected to Outlook")

        try:
            # Get the email by ID
            mail_item = self._namespace.GetItemFromID(email_id)

            # Create reply draft
            reply = mail_item.Reply()

            # Save the draft
            reply.Save()

            draft_id = reply.EntryID

            logger.info(f"Created reply draft for email '{email_id[:20]}...'")
            return draft_id

        except Exception as e:
            error_msg = f"Error creating reply draft: {e}"
            logger.error(error_msg)
            if "not found" in str(e).lower():
                raise OutlookEmailNotFoundException(
                    email_id=email_id,
                    details=error_msg
                )
            raise OutlookConnectionError(
                message=f"Failed to create reply draft",
                details=error_msg
            )

    def delete_email(self, email_id: str) -> bool:
        """
        Delete an email (moves to Deleted Items folder).

        Args:
            email_id: EntryID of the email to delete

        Returns:
            True if successful

        Raises:
            OutlookConnectionError: If not connected
            OutlookEmailNotFoundException: If email not found

        Example:
            connector.delete_email(email.entry_id)
        """
        if not self.is_connected:
            raise OutlookConnectionError("Not connected to Outlook")

        try:
            # Get the email by ID
            mail_item = self._namespace.GetItemFromID(email_id)

            # Delete the email (moves to Deleted Items)
            mail_item.Delete()

            logger.info(f"Deleted email '{email_id[:20]}...'")
            return True

        except Exception as e:
            error_msg = f"Error deleting email: {e}"
            logger.error(error_msg)
            if "not found" in str(e).lower():
                raise OutlookEmailNotFoundException(
                    email_id=email_id,
                    details=error_msg
                )
            raise OutlookConnectionError(
                message=f"Failed to delete email",
                details=error_msg
            )

    def get_accounts(self) -> List['OutlookAccount']:
        """
        Get all email accounts configured in Outlook.

        Returns:
            List of OutlookAccount objects

        Raises:
            OutlookConnectionError: If not connected

        Example:
            connector = OutlookConnector()
            connector.connect()
            accounts = connector.get_accounts()
            for account in accounts:
                print(f"{account.display_name} <{account.email_address}>")
        """
        if not self.is_connected:
            raise OutlookConnectionError("Not connected to Outlook")

        try:
            accounts = []
            outlook_accounts = self._namespace.Accounts

            for i in range(1, outlook_accounts.Count + 1):  # COM uses 1-based indexing
                account = outlook_accounts.Item(i)

                # Extract account properties
                email_address = getattr(account, 'SmtpAddress', '')
                if not email_address:
                    # Fallback to DisplayName if SmtpAddress not available
                    email_address = getattr(account, 'UserName', '')

                display_name = getattr(account, 'DisplayName', '')
                account_type = getattr(account, 'AccountType', 'Unknown')

                # Map account type int to string
                account_type_map = {
                    0: 'Exchange',
                    1: 'IMAP',
                    2: 'POP3',
                    3: 'HTTP',
                    4: 'Other'
                }
                if isinstance(account_type, int):
                    account_type = account_type_map.get(account_type, f'Type-{account_type}')

                outlook_account = OutlookAccount(
                    email_address=email_address,
                    display_name=display_name,
                    account_type=str(account_type),
                    smtp_address=email_address
                )

                accounts.append(outlook_account)

            logger.info(f"Retrieved {len(accounts)} accounts from Outlook")
            return accounts

        except Exception as e:
            error_msg = f"Error retrieving accounts: {e}"
            logger.error(error_msg)
            raise OutlookConnectionError(
                message="Failed to retrieve email accounts",
                details=error_msg
            )

    def disconnect(self):
        """
        Disconnect from Outlook and clean up resources.

        This method releases COM objects and updates connection state.
        It is safe to call even if not currently connected.
        """
        logger.info("Disconnecting from Outlook...")

        try:
            # Release COM objects
            if self._namespace is not None:
                self._namespace = None

            if self._outlook_app is not None:
                self._outlook_app = None

            # Update connection state
            self._connection_state.status = ConnectionStatus.DISCONNECTED
            self._connection_state.retry_count = 0

            logger.info("Disconnected from Outlook")

        except Exception as e:
            logger.warning(f"Error during disconnect: {e}")

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.disconnect()
        except:
            pass
