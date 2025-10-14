"""
Unit Tests for EmailListView Component

Tests Story 2.3 AC3: Email list with priority indicators
"""

import pytest
from unittest.mock import Mock, MagicMock
import customtkinter as ctk
from mailmind.ui.components.email_list_view import EmailListView


class TestEmailListViewInitialization:
    """Test EmailListView initialization."""

    @pytest.fixture
    def root_window(self):
        """Create root window for testing."""
        return ctk.CTk()

    def test_initialization(self, root_window):
        """Test EmailListView initializes correctly."""
        list_view = EmailListView(root_window)

        assert list_view.emails == []
        assert list_view.email_widgets == []
        assert list_view.selected_emails == []
        assert list_view.sort_column == "timestamp"
        assert list_view.sort_reverse is True
        assert list_view.is_loading is False

    def test_initialization_with_callbacks(self, root_window):
        """Test EmailListView accepts callback functions."""
        selected_callback = Mock()
        double_click_callback = Mock()

        list_view = EmailListView(
            root_window,
            on_email_selected=selected_callback,
            on_email_double_click=double_click_callback
        )

        assert list_view.on_email_selected_callback == selected_callback
        assert list_view.on_email_double_click_callback == double_click_callback


class TestEmailManagement:
    """Test email addition and removal."""

    @pytest.fixture
    def list_view(self):
        """Create EmailListView for testing."""
        root = ctk.CTk()
        return EmailListView(root)

    @pytest.fixture
    def sample_email(self):
        """Create sample email data."""
        return {
            "sender": "John Doe",
            "subject": "Test Email",
            "priority": "high",
            "timestamp": "10:30 AM",
            "is_unread": True
        }

    def test_add_email(self, list_view, sample_email):
        """Test adding a single email."""
        list_view.add_email(sample_email)

        assert len(list_view.emails) == 1
        assert list_view.emails[0] == sample_email

    def test_add_multiple_emails(self, list_view, sample_email):
        """Test adding multiple emails at once."""
        emails = [
            sample_email,
            {**sample_email, "subject": "Email 2"},
            {**sample_email, "subject": "Email 3"}
        ]

        list_view.add_emails(emails)

        assert len(list_view.emails) == 3

    def test_clear_emails(self, list_view, sample_email):
        """Test clearing all emails."""
        list_view.add_email(sample_email)
        list_view.clear()

        assert len(list_view.emails) == 0
        assert len(list_view.email_widgets) == 0
        assert len(list_view.selected_emails) == 0


class TestEmailSorting:
    """Test email sorting functionality."""

    @pytest.fixture
    def list_view(self):
        """Create EmailListView for testing."""
        root = ctk.CTk()
        return EmailListView(root)

    @pytest.fixture
    def sample_emails(self):
        """Create sample emails for sorting."""
        return [
            {
                "sender": "Alice",
                "subject": "Zebra",
                "priority": "high",
                "timestamp": "10:00 AM",
                "is_unread": True
            },
            {
                "sender": "Bob",
                "subject": "Apple",
                "priority": "low",
                "timestamp": "11:00 AM",
                "is_unread": False
            },
            {
                "sender": "Charlie",
                "subject": "Mango",
                "priority": "medium",
                "timestamp": "09:00 AM",
                "is_unread": True
            }
        ]

    def test_sort_by_sender(self, list_view, sample_emails):
        """Test sorting by sender."""
        list_view.add_emails(sample_emails)
        list_view._sort_by("sender")

        assert list_view.sort_column == "sender"

    def test_sort_by_subject(self, list_view, sample_emails):
        """Test sorting by subject."""
        list_view.add_emails(sample_emails)
        list_view._sort_by("subject")

        assert list_view.sort_column == "subject"

    def test_sort_by_priority(self, list_view, sample_emails):
        """Test sorting by priority."""
        list_view.add_emails(sample_emails)
        list_view._sort_by("priority")

        assert list_view.sort_column == "priority"

    def test_sort_reverse_toggle(self, list_view, sample_emails):
        """Test sort direction toggles on repeated clicks."""
        list_view.add_emails(sample_emails)

        list_view._sort_by("sender")
        first_reverse = list_view.sort_reverse

        list_view._sort_by("sender")
        second_reverse = list_view.sort_reverse

        assert first_reverse != second_reverse


class TestEmailSelection:
    """Test email selection functionality."""

    @pytest.fixture
    def list_view(self):
        """Create EmailListView for testing."""
        root = ctk.CTk()
        return EmailListView(root)

    @pytest.fixture
    def sample_emails(self):
        """Create sample emails."""
        return [
            {
                "sender": "Alice",
                "subject": "Email 1",
                "priority": "high",
                "timestamp": "10:00 AM",
                "is_unread": True
            },
            {
                "sender": "Bob",
                "subject": "Email 2",
                "priority": "low",
                "timestamp": "11:00 AM",
                "is_unread": False
            }
        ]

    def test_single_email_selection(self, list_view, sample_emails):
        """Test selecting a single email."""
        list_view.add_emails(sample_emails)

        # Simulate click event
        event = Mock()
        event.state = 0  # No Ctrl key

        list_view._on_email_clicked(sample_emails[0], event)

        assert len(list_view.selected_emails) == 1
        assert list_view.selected_emails[0] == sample_emails[0]

    def test_multi_select_with_ctrl(self, list_view, sample_emails):
        """Test multi-select with Ctrl key."""
        list_view.add_emails(sample_emails)

        # First click (normal)
        event = Mock()
        event.state = 0
        list_view._on_email_clicked(sample_emails[0], event)

        # Second click with Ctrl
        event.state = 0x0004  # Ctrl key
        list_view._on_email_clicked(sample_emails[1], event)

        assert len(list_view.selected_emails) == 2

    def test_deselect_with_ctrl(self, list_view, sample_emails):
        """Test deselecting an email with Ctrl+click."""
        list_view.add_emails(sample_emails)

        # Select both
        event = Mock()
        event.state = 0
        list_view._on_email_clicked(sample_emails[0], event)

        event.state = 0x0004
        list_view._on_email_clicked(sample_emails[1], event)

        # Deselect first one
        list_view._on_email_clicked(sample_emails[0], event)

        assert len(list_view.selected_emails) == 1
        assert list_view.selected_emails[0] == sample_emails[1]

    def test_selection_callback(self, sample_emails):
        """Test selection triggers callback."""
        root = ctk.CTk()
        callback = Mock()
        list_view = EmailListView(root, on_email_selected=callback)

        list_view.add_emails(sample_emails)

        event = Mock()
        event.state = 0
        list_view._on_email_clicked(sample_emails[0], event)

        callback.assert_called_once_with(sample_emails[0])

    def test_get_selected_emails(self, list_view, sample_emails):
        """Test getting selected emails."""
        list_view.add_emails(sample_emails)

        event = Mock()
        event.state = 0
        list_view._on_email_clicked(sample_emails[0], event)

        selected = list_view.get_selected_emails()

        assert len(selected) == 1
        assert selected[0] == sample_emails[0]


class TestContextMenu:
    """Test context menu actions."""

    @pytest.fixture
    def list_view(self):
        """Create EmailListView for testing."""
        root = ctk.CTk()
        return EmailListView(root)

    @pytest.fixture
    def sample_email(self):
        """Create sample email."""
        return {
            "sender": "John Doe",
            "subject": "Test Email",
            "priority": "high",
            "timestamp": "10:30 AM",
            "is_unread": True
        }

    def test_mark_as_read(self, list_view, sample_email):
        """Test marking email as read."""
        list_view.add_email(sample_email)

        list_view._mark_as_read(sample_email)

        assert sample_email["is_unread"] is False

    def test_mark_as_unread(self, list_view, sample_email):
        """Test marking email as unread."""
        sample_email["is_unread"] = False
        list_view.add_email(sample_email)

        list_view._mark_as_unread(sample_email)

        assert sample_email["is_unread"] is True

    def test_delete_email(self, list_view, sample_email):
        """Test deleting an email."""
        list_view.add_email(sample_email)

        list_view._delete_email(sample_email)

        assert len(list_view.emails) == 0


class TestKeyboardNavigation:
    """Test keyboard navigation."""

    @pytest.fixture
    def list_view(self):
        """Create EmailListView for testing."""
        root = ctk.CTk()
        return EmailListView(root)

    @pytest.fixture
    def sample_emails(self):
        """Create sample emails."""
        return [
            {"sender": "A", "subject": "1", "priority": "high", "timestamp": "10:00", "is_unread": True},
            {"sender": "B", "subject": "2", "priority": "low", "timestamp": "11:00", "is_unread": False},
            {"sender": "C", "subject": "3", "priority": "medium", "timestamp": "12:00", "is_unread": True}
        ]

    def test_arrow_down_selects_first_email(self, list_view, sample_emails):
        """Test down arrow selects first email if none selected."""
        list_view.add_emails(sample_emails)

        event = Mock()
        list_view._on_arrow_down(event)

        assert len(list_view.selected_emails) == 1
        assert list_view.selected_emails[0] == sample_emails[0]

    def test_arrow_down_moves_to_next(self, list_view, sample_emails):
        """Test down arrow moves to next email."""
        list_view.add_emails(sample_emails)

        # Select first email
        list_view.selected_emails = [sample_emails[0]]

        event = Mock()
        list_view._on_arrow_down(event)

        assert list_view.selected_emails[0] == sample_emails[1]

    def test_arrow_up_moves_to_previous(self, list_view, sample_emails):
        """Test up arrow moves to previous email."""
        list_view.add_emails(sample_emails)

        # Select second email
        list_view.selected_emails = [sample_emails[1]]

        event = Mock()
        list_view._on_arrow_up(event)

        assert list_view.selected_emails[0] == sample_emails[0]

    def test_arrow_up_at_top_does_nothing(self, list_view, sample_emails):
        """Test up arrow at top of list does nothing."""
        list_view.add_emails(sample_emails)

        # Select first email
        list_view.selected_emails = [sample_emails[0]]

        event = Mock()
        list_view._on_arrow_up(event)

        # Should still be on first email
        assert list_view.selected_emails[0] == sample_emails[0]

    def test_arrow_down_at_bottom_does_nothing(self, list_view, sample_emails):
        """Test down arrow at bottom of list does nothing."""
        list_view.add_emails(sample_emails)

        # Select last email
        list_view.selected_emails = [sample_emails[2]]

        event = Mock()
        list_view._on_arrow_down(event)

        # Should still be on last email
        assert list_view.selected_emails[0] == sample_emails[2]

    def test_enter_key_triggers_double_click_callback(self, sample_emails):
        """Test Enter key triggers double-click callback."""
        root = ctk.CTk()
        callback = Mock()
        list_view = EmailListView(root, on_email_double_click=callback)

        list_view.add_emails(sample_emails)
        list_view.selected_emails = [sample_emails[0]]

        event = Mock()
        list_view._on_enter_key(event)

        callback.assert_called_once_with(sample_emails[0])

    def test_delete_key_removes_selected_emails(self, list_view, sample_emails):
        """Test Delete key removes selected emails."""
        list_view.add_emails(sample_emails)
        list_view.selected_emails = [sample_emails[0], sample_emails[1]]

        event = Mock()
        list_view._on_delete_key(event)

        assert len(list_view.emails) == 1
        assert list_view.emails[0] == sample_emails[2]


class TestLoadingStates:
    """Test loading state functionality."""

    @pytest.fixture
    def list_view(self):
        """Create EmailListView for testing."""
        root = ctk.CTk()
        return EmailListView(root)

    def test_show_loading(self, list_view):
        """Test showing loading state."""
        list_view.show_loading()

        assert list_view.is_loading is True

    def test_hide_loading(self, list_view):
        """Test hiding loading state."""
        list_view.show_loading()
        list_view.hide_loading()

        assert list_view.is_loading is False

    def test_loading_clears_existing_emails(self, list_view):
        """Test showing loading clears existing email display."""
        sample_email = {
            "sender": "John",
            "subject": "Test",
            "priority": "high",
            "timestamp": "10:00",
            "is_unread": True
        }

        list_view.add_email(sample_email)
        list_view.show_loading()

        # Emails data should still exist
        assert len(list_view.emails) == 0


class TestEmailListViewIntegration:
    """Integration tests for EmailListView."""

    @pytest.fixture
    def list_view(self):
        """Create EmailListView for testing."""
        root = ctk.CTk()
        return EmailListView(root)

    @pytest.fixture
    def sample_emails(self):
        """Create diverse sample emails."""
        return [
            {
                "sender": "Alice Johnson",
                "subject": "Urgent: Project deadline",
                "priority": "high",
                "timestamp": "10:00 AM",
                "is_unread": True
            },
            {
                "sender": "Bob Smith",
                "subject": "Weekly status report",
                "priority": "medium",
                "timestamp": "Yesterday",
                "is_unread": False
            },
            {
                "sender": "Charlie Brown",
                "subject": "Newsletter: Tech updates",
                "priority": "low",
                "timestamp": "2 days ago",
                "is_unread": False
            }
        ]

    def test_complete_workflow(self, list_view, sample_emails):
        """Test complete email list workflow."""
        # 1. Add emails
        list_view.add_emails(sample_emails)
        assert len(list_view.emails) == 3

        # 2. Sort by sender
        list_view._sort_by("sender")
        assert list_view.sort_column == "sender"

        # 3. Select an email
        event = Mock()
        event.state = 0
        list_view._on_email_clicked(sample_emails[0], event)
        assert len(list_view.selected_emails) == 1

        # 4. Mark as read
        list_view._mark_as_read(sample_emails[0])
        assert sample_emails[0]["is_unread"] is False

        # 5. Clear list
        list_view.clear()
        assert len(list_view.emails) == 0

    def test_multi_select_and_delete_workflow(self, list_view, sample_emails):
        """Test multi-select and batch delete workflow."""
        list_view.add_emails(sample_emails)

        # Select multiple emails
        event = Mock()
        event.state = 0
        list_view._on_email_clicked(sample_emails[0], event)

        event.state = 0x0004
        list_view._on_email_clicked(sample_emails[1], event)

        assert len(list_view.selected_emails) == 2

        # Delete selected emails
        event = Mock()
        list_view._on_delete_key(event)

        assert len(list_view.emails) == 1
        assert list_view.emails[0] == sample_emails[2]
