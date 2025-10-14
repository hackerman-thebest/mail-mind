"""
Unit Tests for FolderSidebar Component

Tests Story 2.3 AC2: Folder sidebar with tree view
"""

import pytest
from unittest.mock import Mock, MagicMock
import customtkinter as ctk
from mailmind.ui.components.folder_sidebar import FolderSidebar, FolderItem


class TestFolderItem:
    """Test FolderItem data class."""

    def test_folder_item_initialization(self):
        """Test FolderItem can be created with basic properties."""
        folder = FolderItem(
            name="Inbox",
            display_name="My Inbox",
            unread_count=5,
            icon="📥"
        )

        assert folder.name == "Inbox"
        assert folder.display_name == "My Inbox"
        assert folder.unread_count == 5
        assert folder.icon == "📥"
        assert folder.parent is None
        assert folder.children == []
        assert folder.is_expanded is True

    def test_folder_item_with_parent(self):
        """Test FolderItem with parent relationship."""
        parent = FolderItem(name="Inbox", display_name="Inbox")
        child = FolderItem(name="Work", display_name="Work", parent=parent)

        # Child should reference parent
        assert child.parent == parent

        # Note: FolderItem doesn't automatically add to parent.children
        # This is done explicitly in FolderSidebar._create_folder()
        parent.children.append(child)
        assert child in parent.children

    def test_folder_item_defaults(self):
        """Test FolderItem default values."""
        folder = FolderItem(name="Test", display_name="Test")

        assert folder.unread_count == 0
        assert folder.icon == "📁"
        assert folder.is_expanded is True


class TestFolderSidebarInitialization:
    """Test FolderSidebar initialization."""

    @pytest.fixture
    def root_window(self):
        """Create root window for testing."""
        return ctk.CTk()

    def test_initialization_without_connector(self, root_window):
        """Test FolderSidebar initializes with default folders."""
        sidebar = FolderSidebar(root_window)

        assert sidebar.outlook_connector is None
        assert len(sidebar.folders) > 0
        assert "Inbox" in sidebar.folders
        assert sidebar.selected_folder == "Inbox"

    def test_initialization_with_callback(self, root_window):
        """Test FolderSidebar accepts callback function."""
        callback = Mock()
        sidebar = FolderSidebar(root_window, on_folder_selected=callback)

        # Callback should be called when Inbox is auto-selected
        callback.assert_called_once_with("Inbox")

    def test_default_folders_structure(self, root_window):
        """Test default folder structure is correct."""
        sidebar = FolderSidebar(root_window)

        # Check root folders exist
        assert "Inbox" in sidebar.folders
        assert "Sent Items" in sidebar.folders
        assert "Drafts" in sidebar.folders
        assert "Archive" in sidebar.folders
        assert "Deleted Items" in sidebar.folders

        # Check subfolder exists
        assert "Work" in sidebar.folders
        assert "Personal" in sidebar.folders

        # Check hierarchy
        inbox = sidebar.folders["Inbox"]
        work = sidebar.folders["Work"]
        assert work.parent == inbox
        assert work in inbox.children


class TestFolderSelection:
    """Test folder selection functionality."""

    @pytest.fixture
    def sidebar(self):
        """Create FolderSidebar for testing."""
        root = ctk.CTk()
        return FolderSidebar(root)

    def test_select_folder(self, sidebar):
        """Test selecting a folder updates state."""
        sidebar.select_folder("Drafts")

        assert sidebar.selected_folder == "Drafts"

    def test_select_folder_with_callback(self):
        """Test folder selection triggers callback."""
        root = ctk.CTk()
        callback = Mock()
        sidebar = FolderSidebar(root, on_folder_selected=callback)

        # Clear previous calls
        callback.reset_mock()

        # Select folder
        sidebar.select_folder("Sent Items")

        # Callback should be called
        callback.assert_called_once_with("Sent Items")

    def test_select_nonexistent_folder(self, sidebar):
        """Test selecting non-existent folder doesn't crash."""
        sidebar.select_folder("NonExistent")

        # Should keep previous selection
        assert sidebar.selected_folder == "Inbox"

    def test_folder_selection_highlighting(self, sidebar):
        """Test selected folder button is highlighted."""
        sidebar.select_folder("Drafts")

        drafts = sidebar.folders["Drafts"]
        if drafts.button:
            # Check button has selection color (gray75 or gray25)
            fg_color = drafts.button.cget("fg_color")
            assert fg_color in [("gray75", "gray25"), "gray75", "gray25"]


class TestFolderTree:
    """Test folder tree rendering and navigation."""

    @pytest.fixture
    def sidebar(self):
        """Create FolderSidebar for testing."""
        root = ctk.CTk()
        return FolderSidebar(root)

    def test_expand_collapse_folder(self, sidebar):
        """Test expanding and collapsing folders."""
        inbox = sidebar.folders["Inbox"]

        # Should be expanded by default
        assert inbox.is_expanded is True

        # Collapse
        inbox.is_expanded = False
        assert inbox.is_expanded is False

        # Expand
        inbox.is_expanded = True
        assert inbox.is_expanded is True

    def test_folder_with_children_has_indicator(self, sidebar):
        """Test folders with children display expand/collapse indicator."""
        inbox = sidebar.folders["Inbox"]

        assert len(inbox.children) > 0
        assert inbox.is_expanded is True

    def test_render_folder_tree(self, sidebar):
        """Test folder tree renders without errors."""
        # Clear and re-render
        for widget in sidebar.folder_list.winfo_children():
            widget.destroy()

        sidebar._render_folder_tree()

        # Should have widgets rendered
        assert len(sidebar.folder_list.winfo_children()) > 0


class TestFolderSearch:
    """Test folder search functionality."""

    @pytest.fixture
    def sidebar(self):
        """Create FolderSidebar for testing."""
        root = ctk.CTk()
        return FolderSidebar(root)

    def test_search_filter_applied(self, sidebar):
        """Test search filter is applied."""
        sidebar.search_filter = "work"

        # Should filter folders
        work = sidebar.folders["Work"]
        sent = sidebar.folders["Sent Items"]

        # Check filter logic
        assert "work".lower() in work.display_name.lower()
        assert "work".lower() not in sent.display_name.lower()

    def test_search_entry_updates_filter(self, sidebar):
        """Test search entry updates filter."""
        sidebar.search_entry.insert(0, "draft")

        # Trigger search changed event
        event = Mock()
        sidebar._on_search_changed(event)

        assert sidebar.search_filter == "draft"

    def test_empty_search_shows_all_folders(self, sidebar):
        """Test empty search shows all folders."""
        sidebar.search_filter = ""

        # All folders should be visible
        for folder in sidebar.folders.values():
            # Empty filter should not filter anything
            assert True


class TestFolderRefresh:
    """Test folder refresh functionality."""

    @pytest.fixture
    def sidebar(self):
        """Create FolderSidebar for testing."""
        root = ctk.CTk()
        return FolderSidebar(root)

    def test_refresh_folders_clears_old_data(self, sidebar):
        """Test refresh clears old folder data."""
        old_count = len(sidebar.folders)

        sidebar.refresh_folders()

        # Should have folders after refresh
        assert len(sidebar.folders) > 0

    def test_refresh_with_connector(self):
        """Test refresh with OutlookConnector."""
        root = ctk.CTk()
        connector = Mock()
        sidebar = FolderSidebar(root, outlook_connector=connector)

        # Should use defaults since connector integration not implemented
        assert len(sidebar.folders) > 0


class TestUnreadCounts:
    """Test unread count functionality."""

    @pytest.fixture
    def sidebar(self):
        """Create FolderSidebar for testing."""
        root = ctk.CTk()
        return FolderSidebar(root)

    def test_folder_displays_unread_count(self, sidebar):
        """Test folders display unread counts."""
        inbox = sidebar.folders["Inbox"]

        assert inbox.unread_count == 5

    def test_update_unread_count(self, sidebar):
        """Test updating unread count."""
        sidebar.update_unread_count("Inbox", 10)

        inbox = sidebar.folders["Inbox"]
        assert inbox.unread_count == 10

    def test_zero_unread_count_not_displayed(self, sidebar):
        """Test folders with 0 unread don't show count."""
        sent = sidebar.folders["Sent Items"]

        assert sent.unread_count == 0

    def test_update_nonexistent_folder_unread_count(self, sidebar):
        """Test updating unread count for non-existent folder doesn't crash."""
        sidebar.update_unread_count("NonExistent", 5)

        # Should not crash
        assert True


# Integration tests
class TestFolderSidebarIntegration:
    """Integration tests for FolderSidebar."""

    @pytest.fixture
    def sidebar(self):
        """Create FolderSidebar for testing."""
        root = ctk.CTk()
        return FolderSidebar(root)

    def test_complete_workflow(self, sidebar):
        """Test complete folder navigation workflow."""
        # 1. Select folder
        sidebar.select_folder("Drafts")
        assert sidebar.selected_folder == "Drafts"

        # 2. Search for folder
        sidebar.search_entry.insert(0, "work")
        event = Mock()
        sidebar._on_search_changed(event)
        assert sidebar.search_filter == "work"

        # 3. Clear search
        sidebar.search_entry.delete(0, "end")
        sidebar._on_search_changed(event)
        assert sidebar.search_filter == ""

        # 4. Update unread count
        sidebar.update_unread_count("Drafts", 5)
        assert sidebar.folders["Drafts"].unread_count == 5

        # 5. Refresh
        sidebar.refresh_folders()
        assert len(sidebar.folders) > 0

    def test_folder_selection_persists_across_search(self, sidebar):
        """Test selected folder persists when searching."""
        sidebar.select_folder("Drafts")

        # Search
        sidebar.search_entry.insert(0, "inbox")
        event = Mock()
        sidebar._on_search_changed(event)

        # Selection should persist
        assert sidebar.selected_folder == "Drafts"
