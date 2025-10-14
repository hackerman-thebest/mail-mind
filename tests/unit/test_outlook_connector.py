"""
Unit tests for OutlookConnector.

Tests cover:
- Connection establishment
- Outlook detection (installed/running)
- Error handling for various scenarios
- Connection state management
- Context manager functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from datetime import datetime
import sys
import platform

# Mock Windows-only imports before importing OutlookConnector
sys.modules['win32com'] = MagicMock()
sys.modules['win32com.client'] = MagicMock()
sys.modules['pywintypes'] = MagicMock()
sys.modules['psutil'] = MagicMock()

# Skip marker for Windows-only tests
skip_on_non_windows = pytest.mark.skipif(
    platform.system() != 'Windows',
    reason="Test requires Windows-specific winreg module"
)

from mailmind.integrations import (
    OutlookConnector,
    OutlookNotInstalledException,
    OutlookNotRunningException,
    OutlookConnectionError,
    OutlookProfileNotConfiguredException,
    OutlookPermissionDeniedException,
    ConnectionStatus,
)


class TestOutlookDetection:
    """Tests for Outlook installation and process detection."""

    @skip_on_non_windows
    @patch('winreg.OpenKey')
    @patch('winreg.CloseKey')
    def test_detect_outlook_installed_via_registry(self, mock_close_key, mock_open_key):
        """Test AC1: Detect Outlook installation via registry check."""
        # Arrange
        mock_key = Mock()
        mock_open_key.return_value = mock_key

        # Act
        result = OutlookConnector.detect_outlook_installed()

        # Assert
        assert result is True
        mock_open_key.assert_called_once()
        mock_close_key.assert_called_once_with(mock_key)

    @skip_on_non_windows
    @patch('winreg.OpenKey')
    def test_detect_outlook_not_installed_registry_error(self, mock_open_key):
        """Test AC1: Detect when Outlook is not installed (registry check fails)."""
        # Arrange
        mock_open_key.side_effect = FileNotFoundError("Key not found")

        # Act
        result = OutlookConnector.detect_outlook_installed()

        # Assert
        assert result is False

    @patch('mailmind.integrations.outlook_connector.psutil')
    def test_is_outlook_running_process_found(self, mock_psutil):
        """Test AC1: Detect Outlook is running via process check."""
        # Arrange
        mock_process = Mock()
        mock_process.info = {'name': 'OUTLOOK.EXE'}
        mock_psutil.process_iter.return_value = [mock_process]

        # Act
        result = OutlookConnector.is_outlook_running()

        # Assert
        assert result is True

    @patch('mailmind.integrations.outlook_connector.psutil')
    def test_is_outlook_not_running_process_not_found(self, mock_psutil):
        """Test AC1: Detect when Outlook is not running."""
        # Arrange
        mock_process = Mock()
        mock_process.info = {'name': 'chrome.exe'}
        mock_psutil.process_iter.return_value = [mock_process]

        # Act
        result = OutlookConnector.is_outlook_running()

        # Assert
        assert result is False

    @patch('mailmind.integrations.outlook_connector.psutil')
    def test_is_outlook_running_handles_access_denied(self, mock_psutil):
        """Test AC1: Handle access denied errors when checking processes."""
        # Arrange
        import psutil
        mock_process = Mock()
        mock_process.info = {'name': 'OUTLOOK.EXE'}

        # First process throws AccessDenied, second one succeeds
        processes = [mock_process]
        mock_psutil.process_iter.return_value = processes
        mock_psutil.AccessDenied = psutil.AccessDenied
        mock_psutil.NoSuchProcess = psutil.NoSuchProcess

        # Act
        result = OutlookConnector.is_outlook_running()

        # Assert
        # Should still work even if some processes throw errors
        assert result is True


class TestOutlookConnection:
    """Tests for Outlook connection establishment."""

    @patch('mailmind.integrations.outlook_connector.win32com')
    @patch('mailmind.integrations.outlook_connector.OutlookConnector.detect_outlook_installed')
    @patch('mailmind.integrations.outlook_connector.OutlookConnector.is_outlook_running')
    def test_connect_success(self, mock_is_running, mock_detect_installed, mock_win32com):
        """Test AC1: Successfully connect to Outlook."""
        # Arrange
        mock_detect_installed.return_value = True
        mock_is_running.return_value = True

        mock_outlook_app = Mock()
        mock_namespace = Mock()
        mock_accounts = Mock()
        mock_accounts.Count = 1

        mock_namespace.Accounts = mock_accounts
        mock_outlook_app.GetNamespace.return_value = mock_namespace
        mock_win32com.client.Dispatch.return_value = mock_outlook_app

        connector = OutlookConnector()

        # Act
        result = connector.connect()

        # Assert
        assert result is True
        assert connector.is_connected is True
        assert connector.connection_state.status == ConnectionStatus.CONNECTED
        assert connector.connection_state.last_connected is not None
        assert connector.connection_state.last_error is None
        mock_win32com.client.Dispatch.assert_called_once_with("Outlook.Application")

    @patch('mailmind.integrations.outlook_connector.OutlookConnector.detect_outlook_installed')
    def test_connect_fails_outlook_not_installed(self, mock_detect_installed):
        """Test AC1: Raise exception when Outlook is not installed."""
        # Arrange
        mock_detect_installed.return_value = False
        connector = OutlookConnector()

        # Act & Assert
        with pytest.raises(OutlookNotInstalledException) as exc_info:
            connector.connect()

        assert "not installed" in str(exc_info.value).lower()
        assert connector.connection_state.last_error is not None

    @patch('mailmind.integrations.outlook_connector.OutlookConnector.detect_outlook_installed')
    @patch('mailmind.integrations.outlook_connector.OutlookConnector.is_outlook_running')
    def test_connect_fails_outlook_not_running(self, mock_is_running, mock_detect_installed):
        """Test AC1: Raise exception when Outlook is not running."""
        # Arrange
        mock_detect_installed.return_value = True
        mock_is_running.return_value = False
        connector = OutlookConnector()

        # Act & Assert
        with pytest.raises(OutlookNotRunningException) as exc_info:
            connector.connect()

        assert "outlook" in str(exc_info.value).lower()
        assert "running" in str(exc_info.value).lower()
        assert connector.connection_state.last_error is not None

    @patch('mailmind.integrations.outlook_connector.win32com')
    @patch('mailmind.integrations.outlook_connector.OutlookConnector.detect_outlook_installed')
    @patch('mailmind.integrations.outlook_connector.OutlookConnector.is_outlook_running')
    @patch('mailmind.integrations.outlook_connector.pywintypes')
    def test_connect_handles_com_error_not_installed(
        self, mock_pywintypes, mock_is_running, mock_detect_installed, mock_win32com
    ):
        """Test AC1: Handle COM error for Outlook not installed (error code -2147221005)."""
        # Arrange
        mock_detect_installed.return_value = True
        mock_is_running.return_value = True

        # Create mock COM error
        class ComError(Exception):
            def __init__(self, code):
                self.args = [code, "Class not registered", None, None]

        mock_pywintypes.com_error = ComError
        mock_win32com.client.Dispatch.side_effect = ComError(-2147221005)

        connector = OutlookConnector()

        # Act & Assert
        with pytest.raises(OutlookNotInstalledException):
            connector.connect()

    @patch('mailmind.integrations.outlook_connector.win32com')
    @patch('mailmind.integrations.outlook_connector.OutlookConnector.detect_outlook_installed')
    @patch('mailmind.integrations.outlook_connector.OutlookConnector.is_outlook_running')
    @patch('mailmind.integrations.outlook_connector.pywintypes')
    def test_connect_handles_com_error_not_running(
        self, mock_pywintypes, mock_is_running, mock_detect_installed, mock_win32com
    ):
        """Test AC1: Handle COM error for Outlook not running (error code -2147023174)."""
        # Arrange
        mock_detect_installed.return_value = True
        mock_is_running.return_value = True

        # Create mock COM error
        class ComError(Exception):
            def __init__(self, code):
                self.args = [code, "RPC server unavailable", None, None]

        mock_pywintypes.com_error = ComError
        mock_win32com.client.Dispatch.side_effect = ComError(-2147023174)

        connector = OutlookConnector()

        # Act & Assert
        with pytest.raises(OutlookNotRunningException):
            connector.connect()

    @patch('mailmind.integrations.outlook_connector.win32com')
    @patch('mailmind.integrations.outlook_connector.OutlookConnector.detect_outlook_installed')
    @patch('mailmind.integrations.outlook_connector.OutlookConnector.is_outlook_running')
    @patch('mailmind.integrations.outlook_connector.pywintypes')
    def test_connect_handles_permission_denied(
        self, mock_pywintypes, mock_is_running, mock_detect_installed, mock_win32com
    ):
        """Test AC1: Handle COM error for permission denied (error code -2147024891)."""
        # Arrange
        mock_detect_installed.return_value = True
        mock_is_running.return_value = True

        class ComError(Exception):
            def __init__(self, code):
                self.args = [code, "Access denied", None, None]

        mock_pywintypes.com_error = ComError
        mock_win32com.client.Dispatch.side_effect = ComError(-2147024891)

        connector = OutlookConnector()

        # Act & Assert
        with pytest.raises(OutlookPermissionDeniedException):
            connector.connect()

    @patch('mailmind.integrations.outlook_connector.win32com')
    @patch('mailmind.integrations.outlook_connector.OutlookConnector.detect_outlook_installed')
    @patch('mailmind.integrations.outlook_connector.OutlookConnector.is_outlook_running')
    def test_connect_no_accounts_configured(
        self, mock_is_running, mock_detect_installed, mock_win32com
    ):
        """Test AC1: Raise exception when no email accounts are configured."""
        # Arrange
        mock_detect_installed.return_value = True
        mock_is_running.return_value = True

        mock_outlook_app = Mock()
        mock_namespace = Mock()
        mock_accounts = Mock()
        mock_accounts.Count = 0  # No accounts configured

        mock_namespace.Accounts = mock_accounts
        mock_outlook_app.GetNamespace.return_value = mock_namespace
        mock_win32com.client.Dispatch.return_value = mock_outlook_app

        connector = OutlookConnector()

        # Act & Assert
        with pytest.raises(OutlookProfileNotConfiguredException):
            connector.connect()


class TestOutlookDisconnection:
    """Tests for Outlook disconnection and cleanup."""

    def test_disconnect_when_connected(self):
        """Test AC1: Successfully disconnect from Outlook."""
        # Arrange
        connector = OutlookConnector()
        connector._outlook_app = Mock()
        connector._namespace = Mock()
        connector._connection_state.status = ConnectionStatus.CONNECTED

        # Act
        connector.disconnect()

        # Assert
        assert connector._outlook_app is None
        assert connector._namespace is None
        assert connector.connection_state.status == ConnectionStatus.DISCONNECTED

    def test_disconnect_when_not_connected(self):
        """Test AC1: Disconnect is safe to call when not connected."""
        # Arrange
        connector = OutlookConnector()

        # Act - should not raise any exceptions
        connector.disconnect()

        # Assert
        assert connector.connection_state.status == ConnectionStatus.DISCONNECTED


class TestConnectionState:
    """Tests for connection state management."""

    def test_initial_connection_state(self):
        """Test AC1: Initial connection state is disconnected."""
        # Arrange & Act
        connector = OutlookConnector()

        # Assert
        assert connector.connection_state.status == ConnectionStatus.DISCONNECTED
        assert connector.is_connected is False
        assert connector.connection_state.last_connected is None
        assert connector.connection_state.last_error is None
        assert connector.connection_state.retry_count == 0

    @patch('mailmind.integrations.outlook_connector.win32com')
    @patch('mailmind.integrations.outlook_connector.OutlookConnector.detect_outlook_installed')
    @patch('mailmind.integrations.outlook_connector.OutlookConnector.is_outlook_running')
    def test_connection_state_updated_on_success(
        self, mock_is_running, mock_detect_installed, mock_win32com
    ):
        """Test AC1: Connection state updated correctly on successful connection."""
        # Arrange
        mock_detect_installed.return_value = True
        mock_is_running.return_value = True

        mock_outlook_app = Mock()
        mock_namespace = Mock()
        mock_accounts = Mock()
        mock_accounts.Count = 1
        mock_namespace.Accounts = mock_accounts
        mock_outlook_app.GetNamespace.return_value = mock_namespace
        mock_win32com.client.Dispatch.return_value = mock_outlook_app

        connector = OutlookConnector()

        # Act
        connector.connect()

        # Assert
        assert connector.connection_state.status == ConnectionStatus.CONNECTED
        assert connector.connection_state.last_connected is not None
        assert connector.connection_state.last_error is None
        assert connector.connection_state.retry_count == 0

    @patch('mailmind.integrations.outlook_connector.OutlookConnector.detect_outlook_installed')
    def test_connection_state_error_stored_on_failure(self, mock_detect_installed):
        """Test AC1: Connection state stores error message on failure."""
        # Arrange
        mock_detect_installed.return_value = False
        connector = OutlookConnector()

        # Act
        try:
            connector.connect()
        except OutlookNotInstalledException:
            pass

        # Assert
        assert connector.connection_state.last_error is not None
        assert "not installed" in connector.connection_state.last_error.lower()


class TestContextManager:
    """Tests for context manager functionality."""

    @patch('mailmind.integrations.outlook_connector.win32com')
    @patch('mailmind.integrations.outlook_connector.OutlookConnector.detect_outlook_installed')
    @patch('mailmind.integrations.outlook_connector.OutlookConnector.is_outlook_running')
    def test_context_manager_connects_and_disconnects(
        self, mock_is_running, mock_detect_installed, mock_win32com
    ):
        """Test AC1: Context manager automatically connects and disconnects."""
        # Arrange
        mock_detect_installed.return_value = True
        mock_is_running.return_value = True

        mock_outlook_app = Mock()
        mock_namespace = Mock()
        mock_accounts = Mock()
        mock_accounts.Count = 1
        mock_namespace.Accounts = mock_accounts
        mock_outlook_app.GetNamespace.return_value = mock_namespace
        mock_win32com.client.Dispatch.return_value = mock_outlook_app

        # Act
        with OutlookConnector() as connector:
            # Assert - inside context
            assert connector.is_connected is True

        # Assert - after context exit
        assert connector.connection_state.status == ConnectionStatus.DISCONNECTED


class TestMultipleConnections:
    """Tests for multiple connection attempts."""

    @patch('mailmind.integrations.outlook_connector.win32com')
    @patch('mailmind.integrations.outlook_connector.OutlookConnector.detect_outlook_installed')
    @patch('mailmind.integrations.outlook_connector.OutlookConnector.is_outlook_running')
    def test_connect_twice_is_idempotent(
        self, mock_is_running, mock_detect_installed, mock_win32com
    ):
        """Test AC1: Calling connect() multiple times is safe (idempotent)."""
        # Arrange
        mock_detect_installed.return_value = True
        mock_is_running.return_value = True

        mock_outlook_app = Mock()
        mock_namespace = Mock()
        mock_accounts = Mock()
        mock_accounts.Count = 1
        mock_namespace.Accounts = mock_accounts
        mock_outlook_app.GetNamespace.return_value = mock_namespace
        mock_win32com.client.Dispatch.return_value = mock_outlook_app

        connector = OutlookConnector()

        # Act
        result1 = connector.connect()
        result2 = connector.connect()

        # Assert
        assert result1 is True
        assert result2 is True
        assert connector.is_connected is True


# Run tests with: pytest tests/unit/test_outlook_connector.py -v
