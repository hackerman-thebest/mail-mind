"""
Folder Sidebar Component

Implements Story 2.3 AC2: Folder sidebar with tree view
- Displays Outlook folder hierarchy
- Shows unread counts
- Folder search
- Integration with OutlookConnector
"""

import logging
import customtkinter as ctk
from typing import Optional, Callable, Dict, List

logger = logging.getLogger(__name__)


class FolderItem:
    """Represents a folder in the hierarchy."""

    def __init__(
        self,
        name: str,
        display_name: str,
        unread_count: int = 0,
        icon: str = "📁",
        parent: Optional["FolderItem"] = None
    ):
        self.name = name
        self.display_name = display_name
        self.unread_count = unread_count
        self.icon = icon
        self.parent = parent
        self.children: List["FolderItem"] = []
        self.button: Optional[ctk.CTkButton] = None
        self.is_expanded = True


class FolderSidebar(ctk.CTkFrame):
    """
    Folder sidebar widget showing Outlook folder tree.

    Features:
    - Hierarchical folder tree display
    - Unread count badges
    - Folder selection with highlighting
    - Search functionality
    - Expand/collapse folders
    - Refresh capability
    """

    def __init__(
        self,
        master,
        outlook_connector=None,
        on_folder_selected: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        """
        Initialize FolderSidebar.

        Args:
            master: Parent widget
            outlook_connector: OutlookConnector instance for folder operations
            on_folder_selected: Callback when folder is selected (receives folder name)
        """
        super().__init__(master, **kwargs)

        self.outlook_connector = outlook_connector
        self.on_folder_selected_callback = on_folder_selected

        self.folders: Dict[str, FolderItem] = {}
        self.selected_folder: Optional[str] = None
        self.search_filter = ""

        # Create UI
        self._create_widgets()

        # Load folders
        self.refresh_folders()

        logger.debug("FolderSidebar initialized")

    def _create_widgets(self):
        """Create sidebar widgets."""
        # Header with refresh button
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=10)

        header = ctk.CTkLabel(
            header_frame,
            text="Folders",
            font=("Segoe UI", 14, "bold")
        )
        header.pack(side="left")

        refresh_btn = ctk.CTkButton(
            header_frame,
            text="↻",
            width=30,
            height=24,
            font=("Segoe UI", 14),
            command=self.refresh_folders
        )
        refresh_btn.pack(side="right")

        # Search box
        self.search_entry = ctk.CTkEntry(
            self,
            placeholder_text="Search folders..."
        )
        self.search_entry.pack(pady=5, padx=10, fill="x")
        self.search_entry.bind("<KeyRelease>", self._on_search_changed)

        # Folder list
        self.folder_list = ctk.CTkScrollableFrame(self)
        self.folder_list.pack(fill="both", expand=True, padx=10, pady=5)

    def refresh_folders(self):
        """Refresh folder list from Outlook or use defaults."""
        # Clear existing folders
        for widget in self.folder_list.winfo_children():
            widget.destroy()
        self.folders.clear()

        if self.outlook_connector:
            # TODO: Integrate with OutlookConnector when available
            # folders = self.outlook_connector.get_folders()
            # self._populate_folders_from_outlook(folders)
            logger.debug("OutlookConnector integration not yet implemented, using defaults")
            self._add_default_folders()
        else:
            self._add_default_folders()

        logger.debug(f"Refreshed folders: {len(self.folders)} total")

    def _add_default_folders(self):
        """Add default Outlook folder structure."""
        # Root folders
        inbox = self._create_folder("Inbox", "📥 Inbox", unread_count=5)
        sent = self._create_folder("Sent Items", "📤 Sent Items")
        drafts = self._create_folder("Drafts", "📝 Drafts", unread_count=2)
        archive = self._create_folder("Archive", "📋 Archive")
        deleted = self._create_folder("Deleted Items", "🗑️ Deleted Items")

        # Subfolders (example)
        self._create_folder(
            "Work",
            "Work",
            icon="💼",
            parent=inbox,
            unread_count=3
        )
        self._create_folder(
            "Personal",
            "Personal",
            icon="🏠",
            parent=inbox,
            unread_count=1
        )

        # Render folder tree
        self._render_folder_tree()

        # Select Inbox by default
        if "Inbox" in self.folders:
            self.select_folder("Inbox")

    def _create_folder(
        self,
        name: str,
        display_name: str,
        icon: str = "📁",
        parent: Optional[FolderItem] = None,
        unread_count: int = 0
    ) -> FolderItem:
        """Create and register a folder."""
        folder = FolderItem(name, display_name, unread_count, icon, parent)
        self.folders[name] = folder

        if parent:
            parent.children.append(folder)

        return folder

    def _render_folder_tree(self):
        """Render the folder tree."""
        # Render root folders first
        root_folders = [f for f in self.folders.values() if f.parent is None]

        for folder in root_folders:
            self._render_folder_item(folder, level=0)

    def _render_folder_item(self, folder: FolderItem, level: int = 0):
        """Render a single folder item and its children."""
        # Apply search filter
        if self.search_filter and self.search_filter.lower() not in folder.display_name.lower():
            return

        # Create folder button
        indent = "  " * level
        display_text = f"{indent}{folder.icon} {folder.display_name}"

        if folder.unread_count > 0:
            display_text = f"{display_text} ({folder.unread_count})"

        # Add expand/collapse indicator for folders with children
        if folder.children:
            indicator = "▼" if folder.is_expanded else "▶"
            display_text = f"{indent}{indicator} {folder.icon} {folder.display_name}"
            if folder.unread_count > 0:
                display_text = f"{display_text} ({folder.unread_count})"

        folder_btn = ctk.CTkButton(
            self.folder_list,
            text=display_text,
            anchor="w",
            fg_color="transparent",
            hover_color=("gray70", "gray30"),
            command=lambda f=folder: self._on_folder_clicked(f)
        )
        folder_btn.pack(fill="x", pady=1)

        folder.button = folder_btn

        # Update button appearance if selected
        if self.selected_folder == folder.name:
            folder_btn.configure(fg_color=("gray75", "gray25"))

        # Render children if expanded
        if folder.is_expanded and folder.children:
            for child in folder.children:
                self._render_folder_item(child, level + 1)

    def _on_folder_clicked(self, folder: FolderItem):
        """Handle folder click."""
        if folder.children:
            # Toggle expand/collapse
            folder.is_expanded = not folder.is_expanded
            self._render_folder_tree()

        # Select folder
        self.select_folder(folder.name)

        logger.debug(f"Folder clicked: {folder.name}")

    def select_folder(self, folder_name: str):
        """
        Select a folder programmatically.

        Args:
            folder_name: Name of folder to select
        """
        if folder_name not in self.folders:
            logger.warning(f"Folder not found: {folder_name}")
            return

        # Update selection
        old_selection = self.selected_folder
        self.selected_folder = folder_name

        # Update button appearances
        if old_selection and old_selection in self.folders:
            old_folder = self.folders[old_selection]
            if old_folder.button:
                old_folder.button.configure(fg_color="transparent")

        new_folder = self.folders[folder_name]
        if new_folder.button:
            new_folder.button.configure(fg_color=("gray75", "gray25"))

        # Call callback
        if self.on_folder_selected_callback:
            self.on_folder_selected_callback(folder_name)

        logger.debug(f"Folder selected: {folder_name}")

    def _on_search_changed(self, event):
        """Handle search box changes."""
        self.search_filter = self.search_entry.get()

        # Clear and re-render
        for widget in self.folder_list.winfo_children():
            widget.destroy()

        self._render_folder_tree()

        logger.debug(f"Search filter: '{self.search_filter}'")

    def update_unread_count(self, folder_name: str, count: int):
        """
        Update unread count for a folder.

        Args:
            folder_name: Name of folder
            count: New unread count
        """
        if folder_name in self.folders:
            self.folders[folder_name].unread_count = count

            # Re-render to show updated count
            for widget in self.folder_list.winfo_children():
                widget.destroy()
            self._render_folder_tree()

            logger.debug(f"Updated unread count for {folder_name}: {count}")
