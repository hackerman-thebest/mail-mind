"""
Main Window for MailMind Application

Implements Story 2.3 AC2 & AC7: Main Window Layout with Resizable Panels
- 3-column layout: Folder Sidebar | Email List | Analysis Panel
- Resizable splitters with persistence
- Panel collapse/expand functionality
- Menu bar with keyboard shortcuts
- Window state persistence (size, position, maximized state)

Usage:
    app = MainWindow(
        theme_manager=theme_mgr,
        db_manager=db,
        outlook_connector=outlook,
        email_engine=engine
    )
    app.mainloop()
"""

import logging
import customtkinter as ctk
from typing import Optional
from pathlib import Path

from mailmind.ui.components.toast import ToastManager

logger = logging.getLogger(__name__)


class MainWindow(ctk.CTk):
    """
    Main application window for MailMind.

    Layout:
    ┌────────────────────────────────────────────────────────────┐
    │ Menu Bar                                                   │
    ├──────────┬────────────────────────┬────────────────────────┤
    │          │                        │                        │
    │ Folder   │   Email List View      │   Analysis Panel       │
    │ Sidebar  │   (with priority       │   (AI analysis         │
    │ (200px)  │    indicators)         │    display)            │
    │          │                        │   (400px)              │
    │          │                        │                        │
    ├──────────┴────────────────────────┴────────────────────────┤
    │ Status Bar (Ollama, Outlook, Performance)                  │
    └────────────────────────────────────────────────────────────┘
    """

    # Window configuration
    DEFAULT_WIDTH = 1200
    DEFAULT_HEIGHT = 800
    MIN_WIDTH = 800
    MIN_HEIGHT = 600

    # Panel configuration
    SIDEBAR_DEFAULT_WIDTH = 200
    SIDEBAR_MIN_WIDTH = 150
    ANALYSIS_DEFAULT_WIDTH = 400
    ANALYSIS_MIN_WIDTH = 300
    EMAIL_LIST_MIN_WIDTH = 300

    def __init__(
        self,
        theme_manager=None,
        db_manager=None,
        outlook_connector=None,
        email_engine=None,
        **kwargs
    ):
        """
        Initialize MainWindow.

        Args:
            theme_manager: ThemeManager instance for theme control
            db_manager: DatabaseManager instance for persistence
            outlook_connector: OutlookConnector instance for email operations
            email_engine: EmailAnalysisEngine instance for AI analysis
        """
        super().__init__(**kwargs)

        self.theme_manager = theme_manager
        self.db_manager = db_manager
        self.outlook_connector = outlook_connector
        self.email_engine = email_engine

        # Window state
        self._sidebar_collapsed = False
        self._analysis_collapsed = False

        # Initialize toast manager for notifications
        self.toast_manager = None  # Initialized after window is created

        # Configure window
        self._setup_window()

        # Create UI components
        self._create_menu_bar()
        self._create_main_layout()
        self._create_status_bar()

        # Initialize toast manager (after window is fully created)
        self.toast_manager = ToastManager(self)

        # Restore saved layout
        self._restore_layout()

        # Register theme observer
        if self.theme_manager:
            self.theme_manager.add_observer(self._on_theme_changed)

        logger.info("MainWindow initialized")

    def _setup_window(self):
        """Configure window properties."""
        self.title("MailMind - Sovereign AI Email Assistant")
        self.geometry(f"{self.DEFAULT_WIDTH}x{self.DEFAULT_HEIGHT}")
        self.minsize(self.MIN_WIDTH, self.MIN_HEIGHT)

        # Set window icon if available
        icon_path = Path(__file__).parent.parent.parent.parent / "assets" / "icon.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception as e:
                logger.warning(f"Failed to set window icon: {e}")

        # Handle window close event
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_menu_bar(self):
        """Create menu bar with File, Edit, View, Tools, Help menus."""
        # Note: CustomTkinter doesn't have native menu bar support
        # We'll create a custom menu bar using frames and buttons
        self.menu_frame = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.menu_frame.pack(fill="x", side="top")

        # File menu button
        file_btn = ctk.CTkButton(
            self.menu_frame,
            text="File",
            width=60,
            height=25,
            corner_radius=0,
            fg_color="transparent",
            hover_color=("gray70", "gray30"),
            command=self._show_file_menu
        )
        file_btn.pack(side="left", padx=2)

        # Edit menu button
        edit_btn = ctk.CTkButton(
            self.menu_frame,
            text="Edit",
            width=60,
            height=25,
            corner_radius=0,
            fg_color="transparent",
            hover_color=("gray70", "gray30"),
            command=self._show_edit_menu
        )
        edit_btn.pack(side="left", padx=2)

        # View menu button
        view_btn = ctk.CTkButton(
            self.menu_frame,
            text="View",
            width=60,
            height=25,
            corner_radius=0,
            fg_color="transparent",
            hover_color=("gray70", "gray30"),
            command=self._show_view_menu
        )
        view_btn.pack(side="left", padx=2)

        # Tools menu button
        tools_btn = ctk.CTkButton(
            self.menu_frame,
            text="Tools",
            width=60,
            height=25,
            corner_radius=0,
            fg_color="transparent",
            hover_color=("gray70", "gray30"),
            command=self._show_tools_menu
        )
        tools_btn.pack(side="left", padx=2)

        # Help menu button
        help_btn = ctk.CTkButton(
            self.menu_frame,
            text="Help",
            width=60,
            height=25,
            corner_radius=0,
            fg_color="transparent",
            hover_color=("gray70", "gray30"),
            command=self._show_help_menu
        )
        help_btn.pack(side="left", padx=2)

        logger.debug("Menu bar created")

    def _create_main_layout(self):
        """Create 3-column layout with resizable panels."""
        # Main content container (between menu and status bar)
        self.content_frame = ctk.CTkFrame(self, corner_radius=0)
        self.content_frame.pack(fill="both", expand=True)

        # Create panels (using frames for now - will be replaced with actual components)
        # Left panel: Folder Sidebar
        self.sidebar_frame = ctk.CTkFrame(
            self.content_frame,
            width=self.SIDEBAR_DEFAULT_WIDTH,
            corner_radius=0
        )
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_frame.pack_propagate(False)  # Maintain fixed width

        # Sidebar header
        sidebar_header = ctk.CTkLabel(
            self.sidebar_frame,
            text="Folders",
            font=("Segoe UI", 14, "bold")
        )
        sidebar_header.pack(pady=10)

        # Center panel: Email List View
        self.email_list_frame = ctk.CTkFrame(self.content_frame, corner_radius=0)
        self.email_list_frame.pack(side="left", fill="both", expand=True)

        # Email list header
        email_list_header = ctk.CTkLabel(
            self.email_list_frame,
            text="Inbox",
            font=("Segoe UI", 14, "bold")
        )
        email_list_header.pack(pady=10)

        # Right panel: Analysis Panel
        self.analysis_frame = ctk.CTkFrame(
            self.content_frame,
            width=self.ANALYSIS_DEFAULT_WIDTH,
            corner_radius=0
        )
        self.analysis_frame.pack(side="right", fill="y")
        self.analysis_frame.pack_propagate(False)  # Maintain fixed width

        # Analysis panel header
        analysis_header = ctk.CTkLabel(
            self.analysis_frame,
            text="Analysis",
            font=("Segoe UI", 14, "bold")
        )
        analysis_header.pack(pady=10)

        logger.debug("Main layout created with 3 panels")

    def _create_status_bar(self):
        """Create status bar at bottom of window."""
        self.status_bar_frame = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.status_bar_frame.pack(fill="x", side="bottom")

        # Ollama status
        self.ollama_status = ctk.CTkLabel(
            self.status_bar_frame,
            text="🟢 Ollama: Connected",
            font=("Segoe UI", 10)
        )
        self.ollama_status.pack(side="left", padx=10)

        # Outlook status
        self.outlook_status = ctk.CTkLabel(
            self.status_bar_frame,
            text="🟢 Outlook: Connected",
            font=("Segoe UI", 10)
        )
        self.outlook_status.pack(side="left", padx=10)

        # Processing queue
        self.queue_status = ctk.CTkLabel(
            self.status_bar_frame,
            text="Queue: 0/0",
            font=("Segoe UI", 10)
        )
        self.queue_status.pack(side="left", padx=10)

        # Token speed
        self.token_speed = ctk.CTkLabel(
            self.status_bar_frame,
            text="Speed: 0 tok/s",
            font=("Segoe UI", 10)
        )
        self.token_speed.pack(side="right", padx=10)

        logger.debug("Status bar created")

    def _restore_layout(self):
        """Restore saved window layout from database."""
        if not self.db_manager:
            return

        try:
            # Restore window size
            width = self.db_manager.get_preference("window_width")
            height = self.db_manager.get_preference("window_height")
            if width and height:
                self.geometry(f"{width}x{height}")
                logger.debug(f"Restored window size: {width}x{height}")

            # Restore window state (maximized)
            is_maximized = self.db_manager.get_preference("window_maximized")
            if is_maximized:
                self.state("zoomed")  # Windows maximize
                logger.debug("Restored maximized state")

            # Restore panel widths
            sidebar_width = self.db_manager.get_preference("sidebar_width")
            if sidebar_width:
                self.sidebar_frame.configure(width=sidebar_width)

            analysis_width = self.db_manager.get_preference("analysis_width")
            if analysis_width:
                self.analysis_frame.configure(width=analysis_width)

        except Exception as e:
            logger.warning(f"Failed to restore layout: {e}")

    def _save_layout(self):
        """Save current window layout to database."""
        if not self.db_manager:
            return

        try:
            # Save window size
            geometry = self.geometry()
            width, height = geometry.split("+")[0].split("x")
            self.db_manager.set_preference("window_width", int(width))
            self.db_manager.set_preference("window_height", int(height))

            # Save maximized state
            is_maximized = self.state() == "zoomed"
            self.db_manager.set_preference("window_maximized", is_maximized)

            # Save panel widths
            sidebar_width = self.sidebar_frame.winfo_width()
            self.db_manager.set_preference("sidebar_width", sidebar_width)

            analysis_width = self.analysis_frame.winfo_width()
            self.db_manager.set_preference("analysis_width", analysis_width)

            logger.debug("Layout saved to database")

        except Exception as e:
            logger.error(f"Failed to save layout: {e}")

    def toggle_sidebar(self):
        """Toggle folder sidebar visibility."""
        if self._sidebar_collapsed:
            self.sidebar_frame.pack(side="left", fill="y", before=self.email_list_frame)
            self._sidebar_collapsed = False
            logger.debug("Sidebar expanded")
        else:
            self.sidebar_frame.pack_forget()
            self._sidebar_collapsed = True
            logger.debug("Sidebar collapsed")

    def toggle_analysis_panel(self):
        """Toggle analysis panel visibility."""
        if self._analysis_collapsed:
            self.analysis_frame.pack(side="right", fill="y")
            self._analysis_collapsed = False
            logger.debug("Analysis panel expanded")
        else:
            self.analysis_frame.pack_forget()
            self._analysis_collapsed = True
            logger.debug("Analysis panel collapsed")

    def show_security_blocked_notification(self, pattern_name: str, severity: str = "high", email_subject: str = None):
        """
        Show toast notification when email is blocked for security.

        Story 3.2 AC4, AC6: User notification toast when email is blocked.

        Args:
            pattern_name: Name of security pattern that triggered block
            severity: Severity level (high/medium/low)
            email_subject: Subject of blocked email (optional)
        """
        if not self.toast_manager:
            logger.warning("ToastManager not initialized")
            return

        # Construct user-friendly message
        subject_text = f": {email_subject[:30]}" if email_subject else ""
        message = f"Email blocked for security{subject_text}\nReason: {pattern_name.replace('_', ' ').title()}"

        # Show error toast (red)
        self.toast_manager.show(
            message=message,
            toast_type="error",
            duration=5000  # 5 seconds for security notifications
        )

        logger.info(f"Security notification shown: {pattern_name} (severity: {severity})")

    def show_security_warning_notification(self, pattern_name: str, email_subject: str = None):
        """
        Show toast notification when email has security warning but is allowed.

        Story 3.2 AC6: User notification for warned emails (Permissive mode).

        Args:
            pattern_name: Name of security pattern that triggered warning
            email_subject: Subject of email (optional)
        """
        if not self.toast_manager:
            logger.warning("ToastManager not initialized")
            return

        # Construct user-friendly message
        subject_text = f": {email_subject[:30]}" if email_subject else ""
        message = f"Security warning{subject_text}\nPattern: {pattern_name.replace('_', ' ').title()}"

        # Show info toast (blue)
        self.toast_manager.show(
            message=message,
            toast_type="info",
            duration=4000  # 4 seconds for warnings
        )

        logger.info(f"Security warning shown: {pattern_name}")

    def _on_theme_changed(self, old_theme, new_theme):
        """Handle theme change event."""
        logger.info(f"Theme changed: {old_theme} → {new_theme}")
        # UI components will automatically update via CustomTkinter

    def _on_closing(self):
        """Handle window close event."""
        logger.info("MainWindow closing")

        # Save layout before closing
        self._save_layout()

        # Clean up resources
        if self.theme_manager:
            self.theme_manager.remove_observer(self._on_theme_changed)

        # Close window
        self.destroy()

    # Menu command handlers (stubs for now)
    def _show_file_menu(self):
        """Show File menu."""
        logger.debug("File menu clicked")

    def _show_edit_menu(self):
        """Show Edit menu."""
        logger.debug("Edit menu clicked")

    def _show_view_menu(self):
        """Show View menu."""
        logger.debug("View menu clicked")

    def _show_tools_menu(self):
        """Show Tools menu."""
        logger.debug("Tools menu clicked")

    def _show_help_menu(self):
        """Show Help menu."""
        logger.debug("Help menu clicked")


def main():
    """Demo/test main window."""
    # Set appearance mode
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # Create main window
    app = MainWindow()

    # Run application
    app.mainloop()


if __name__ == "__main__":
    main()
