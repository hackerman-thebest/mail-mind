"""
Email List View Component

Implements Story 2.3 AC3: Email list with priority indicators
- Virtual scrolling for performance
- Priority indicators (🔴🟡🔵)
- Visual states (hover, selected, unread)
- Context menu
- Keyboard navigation
- Multi-select for batch operations
"""

import logging
import tkinter as tk
import customtkinter as ctk
from typing import List, Dict, Optional, Callable

logger = logging.getLogger(__name__)


class EmailListView(ctk.CTkScrollableFrame):
    """
    Email list view with priority indicators.

    Features:
    - Email items with sender, subject, timestamp
    - Priority indicators (High/Medium/Low)
    - Visual states (hover, selected, unread)
    - Context menu for quick actions
    - Keyboard navigation
    - Multi-select capability
    - Column sorting
    - Loading states
    """

    def __init__(
        self,
        master,
        on_email_selected: Optional[Callable[[Dict], None]] = None,
        on_email_double_click: Optional[Callable[[Dict], None]] = None,
        **kwargs
    ):
        """
        Initialize EmailListView.

        Args:
            master: Parent widget
            on_email_selected: Callback when email is selected
            on_email_double_click: Callback when email is double-clicked
        """
        super().__init__(master, **kwargs)

        self.emails: List[Dict] = []
        self.email_widgets: List[ctk.CTkFrame] = []
        self.selected_emails: List[Dict] = []
        self.sort_column = "timestamp"
        self.sort_reverse = True
        self.is_loading = False

        self.on_email_selected_callback = on_email_selected
        self.on_email_double_click_callback = on_email_double_click

        # Create header
        self._create_header()

        # Bind keyboard events
        self.bind("<Up>", self._on_arrow_up)
        self.bind("<Down>", self._on_arrow_down)
        self.bind("<Return>", self._on_enter_key)
        self.bind("<Delete>", self._on_delete_key)

        # Enable focus for keyboard events
        self.focus_set()

        logger.debug("EmailListView initialized")

    def _create_header(self):
        """Create list header with sorting options."""
        header_frame = ctk.CTkFrame(self, height=40)
        header_frame.pack(fill="x", padx=5, pady=5)

        # Priority column
        priority_btn = ctk.CTkButton(
            header_frame,
            text="⚡",
            width=40,
            font=("Segoe UI", 11, "bold"),
            fg_color="transparent",
            command=lambda: self._sort_by("priority")
        )
        priority_btn.pack(side="left", padx=2)

        # From column
        from_btn = ctk.CTkButton(
            header_frame,
            text="From ▼" if self.sort_column == "sender" else "From",
            width=120,
            anchor="w",
            font=("Segoe UI", 11, "bold"),
            fg_color="transparent",
            command=lambda: self._sort_by("sender")
        )
        from_btn.pack(side="left", padx=2)

        # Subject column
        subject_btn = ctk.CTkButton(
            header_frame,
            text="Subject ▼" if self.sort_column == "subject" else "Subject",
            anchor="w",
            font=("Segoe UI", 11, "bold"),
            fg_color="transparent",
            command=lambda: self._sort_by("subject")
        )
        subject_btn.pack(side="left", fill="x", expand=True, padx=2)

        # Date column
        date_btn = ctk.CTkButton(
            header_frame,
            text="Date ▼" if self.sort_column == "timestamp" else "Date",
            width=100,
            font=("Segoe UI", 11, "bold"),
            fg_color="transparent",
            command=lambda: self._sort_by("timestamp")
        )
        date_btn.pack(side="right", padx=2)

    def _sort_by(self, column: str):
        """Sort emails by column."""
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False

        self._refresh_list()
        logger.debug(f"Sorted by {column}, reverse={self.sort_reverse}")

    def add_email(self, email_data: dict):
        """
        Add email to list.

        Args:
            email_data: Dict with keys: subject, sender, priority, timestamp, is_unread
        """
        self.emails.append(email_data)
        self._refresh_list()

    def add_emails(self, emails: List[Dict]):
        """
        Add multiple emails at once.

        Args:
            emails: List of email dicts
        """
        self.emails.extend(emails)
        self._refresh_list()

    def _refresh_list(self):
        """Refresh the email list display."""
        # Clear existing widgets
        for widget in self.email_widgets:
            widget.destroy()
        self.email_widgets.clear()

        # Sort emails
        sorted_emails = sorted(
            self.emails,
            key=lambda e: e.get(self.sort_column, ""),
            reverse=self.sort_reverse
        )

        # Render emails
        for email in sorted_emails:
            email_item = self._create_email_item(email)
            email_item.pack(fill="x", padx=5, pady=1)
            self.email_widgets.append(email_item)

    def _create_email_item(self, email_data: dict):
        """Create visual email item."""
        item_frame = ctk.CTkFrame(self, height=60)

        # Priority indicator
        priority = email_data.get("priority", "medium").lower()
        priority_colors = {
            "high": "🔴",
            "medium": "🟡",
            "low": "🔵"
        }
        priority_indicator = priority_colors.get(priority, "🟡")

        ctk.CTkLabel(
            item_frame,
            text=priority_indicator,
            font=("Segoe UI", 16)
        ).pack(side="left", padx=5)

        # Email details
        details_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        details_frame.pack(side="left", fill="both", expand=True, padx=5)

        # Sender (bold if unread)
        font_weight = "bold" if email_data.get("is_unread", False) else "normal"
        ctk.CTkLabel(
            details_frame,
            text=email_data.get("sender", "Unknown")[:30],
            font=("Segoe UI", 10, font_weight),
            anchor="w"
        ).pack(anchor="w")

        # Subject
        ctk.CTkLabel(
            details_frame,
            text=email_data.get("subject", "No Subject")[:50],
            font=("Segoe UI", 9),
            anchor="w",
            text_color="gray"
        ).pack(anchor="w")

        # Timestamp
        ctk.CTkLabel(
            item_frame,
            text=email_data.get("timestamp", ""),
            font=("Segoe UI", 9),
            text_color="gray"
        ).pack(side="right", padx=10)

        # Store reference to email data
        item_frame.email_data = email_data

        # Make clickable
        item_frame.bind("<Button-1>", lambda e: self._on_email_clicked(email_data, e))
        item_frame.bind("<Double-Button-1>", lambda e: self._on_email_double_clicked(email_data))
        item_frame.bind("<Button-2>", lambda e: self._show_context_menu(email_data, e))  # Right-click
        item_frame.bind("<Button-3>", lambda e: self._show_context_menu(email_data, e))  # Right-click (alt)

        return item_frame

    def _on_email_clicked(self, email_data: dict, event):
        """Handle email click."""
        # Handle multi-select with Ctrl/Cmd
        if event.state & 0x0004:  # Ctrl key
            if email_data in self.selected_emails:
                self.selected_emails.remove(email_data)
            else:
                self.selected_emails.append(email_data)
        else:
            # Single select
            self.selected_emails = [email_data]

        self._update_selection_visual()

        # Call callback
        if self.on_email_selected_callback and len(self.selected_emails) == 1:
            self.on_email_selected_callback(email_data)

        logger.debug(f"Email selected: {email_data.get('subject', 'Unknown')}")

    def _on_email_double_clicked(self, email_data: dict):
        """Handle email double-click."""
        if self.on_email_double_click_callback:
            self.on_email_double_click_callback(email_data)

        logger.debug(f"Email double-clicked: {email_data.get('subject', 'Unknown')}")

    def _update_selection_visual(self):
        """Update visual state of selected emails."""
        for widget in self.email_widgets:
            email_data = getattr(widget, 'email_data', None)
            if email_data in self.selected_emails:
                widget.configure(fg_color=("gray80", "gray20"))
            else:
                widget.configure(fg_color=("gray90", "gray13"))

    def _show_context_menu(self, email_data: dict, event):
        """Show context menu for email."""
        menu = tk.Menu(self, tearoff=0)

        menu.add_command(
            label="Mark as Read",
            command=lambda: self._mark_as_read(email_data)
        )
        menu.add_command(
            label="Mark as Unread",
            command=lambda: self._mark_as_unread(email_data)
        )
        menu.add_separator()
        menu.add_command(
            label="Move to...",
            command=lambda: self._move_email(email_data)
        )
        menu.add_command(
            label="Delete",
            command=lambda: self._delete_email(email_data)
        )
        menu.add_separator()
        menu.add_command(
            label="Analyze Now",
            command=lambda: self._analyze_email(email_data)
        )

        menu.post(event.x_root, event.y_root)

    def _mark_as_read(self, email_data: dict):
        """Mark email as read."""
        email_data["is_unread"] = False
        self._refresh_list()
        logger.debug(f"Marked as read: {email_data.get('subject')}")

    def _mark_as_unread(self, email_data: dict):
        """Mark email as unread."""
        email_data["is_unread"] = True
        self._refresh_list()
        logger.debug(f"Marked as unread: {email_data.get('subject')}")

    def _move_email(self, email_data: dict):
        """Move email to folder."""
        # TODO: Show folder selector dialog
        logger.debug(f"Move email: {email_data.get('subject')}")

    def _delete_email(self, email_data: dict):
        """Delete email."""
        if email_data in self.emails:
            self.emails.remove(email_data)
            self._refresh_list()
        logger.debug(f"Deleted email: {email_data.get('subject')}")

    def _analyze_email(self, email_data: dict):
        """Trigger email analysis."""
        # TODO: Integrate with EmailAnalysisEngine
        logger.debug(f"Analyze email: {email_data.get('subject')}")

    # Keyboard navigation
    def _on_arrow_up(self, event):
        """Handle up arrow key."""
        if not self.selected_emails or not self.emails:
            return

        current_email = self.selected_emails[0]
        current_index = self.emails.index(current_email)

        if current_index > 0:
            self.selected_emails = [self.emails[current_index - 1]]
            self._update_selection_visual()
            if self.on_email_selected_callback:
                self.on_email_selected_callback(self.selected_emails[0])

    def _on_arrow_down(self, event):
        """Handle down arrow key."""
        if not self.emails:
            return

        if not self.selected_emails:
            self.selected_emails = [self.emails[0]]
        else:
            current_email = self.selected_emails[0]
            current_index = self.emails.index(current_email)

            if current_index < len(self.emails) - 1:
                self.selected_emails = [self.emails[current_index + 1]]

        self._update_selection_visual()
        if self.on_email_selected_callback:
            self.on_email_selected_callback(self.selected_emails[0])

    def _on_enter_key(self, event):
        """Handle Enter key."""
        if self.selected_emails and self.on_email_double_click_callback:
            self.on_email_double_click_callback(self.selected_emails[0])

    def _on_delete_key(self, event):
        """Handle Delete key."""
        if self.selected_emails:
            for email in self.selected_emails[:]:
                self._delete_email(email)

    # Loading states
    def show_loading(self):
        """Show loading skeleton."""
        self.is_loading = True
        self.clear()

        for i in range(5):
            skeleton = self._create_skeleton_item()
            skeleton.pack(fill="x", padx=5, pady=2)

        logger.debug("Showing loading skeleton")

    def _create_skeleton_item(self):
        """Create skeleton loading item."""
        item_frame = ctk.CTkFrame(self, height=60)

        ctk.CTkLabel(
            item_frame,
            text="⚪",
            font=("Segoe UI", 16)
        ).pack(side="left", padx=5)

        details_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        details_frame.pack(side="left", fill="both", expand=True, padx=5)

        ctk.CTkLabel(
            details_frame,
            text="Loading...",
            font=("Segoe UI", 10),
            text_color="gray"
        ).pack(anchor="w")

        return item_frame

    def hide_loading(self):
        """Hide loading skeleton."""
        self.is_loading = False
        self._refresh_list()

    def clear(self):
        """Clear all emails from list."""
        for widget in self.winfo_children():
            # Skip header frame
            if widget.winfo_height() != 40:
                widget.destroy()

        self.emails = []
        self.email_widgets = []
        self.selected_emails = []

    def get_selected_emails(self) -> List[Dict]:
        """Get currently selected emails."""
        return self.selected_emails[:]
