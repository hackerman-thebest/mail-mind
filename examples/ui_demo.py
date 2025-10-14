"""
MailMind UI Demo

Demonstrates Story 2.3: CustomTkinter UI Framework
- Main window with 3-panel layout
- Theme management (dark/light toggle)
- Basic UI components
- Toast notifications
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import customtkinter as ctk
from mailmind.ui.theme_manager import ThemeManager
from mailmind.ui.components.folder_sidebar import FolderSidebar
from mailmind.ui.components.email_list_view import EmailListView
from mailmind.ui.components.analysis_panel import AnalysisPanel
from mailmind.ui.components.toast import ToastManager


class MailMindDemo(ctk.CTk):
    """Demo application showing MailMind UI components."""

    def __init__(self):
        super().__init__()

        # Configure window
        self.title("MailMind UI Demo - Story 2.3")
        self.geometry("1200x800")
        self.minsize(800, 600)

        # Initialize theme manager (without database)
        self.theme_mgr = ThemeManager(db_manager=None)

        # Initialize toast manager
        self.toast_mgr = ToastManager(self)

        # Create UI
        self._create_ui()

        # Show welcome toast
        self.after(500, lambda: self.toast_mgr.show(
            "Welcome to MailMind!",
            toast_type="success",
            duration=3000
        ))

    def _create_ui(self):
        """Create demo UI."""
        # Menu bar
        menu_frame = ctk.CTkFrame(self, height=30, corner_radius=0)
        menu_frame.pack(fill="x", side="top")

        ctk.CTkLabel(
            menu_frame,
            text="MailMind - Demo Mode",
            font=("Segoe UI", 12, "bold")
        ).pack(side="left", padx=10)

        # Theme toggle button
        theme_btn = ctk.CTkButton(
            menu_frame,
            text="Toggle Theme",
            width=120,
            command=self._toggle_theme
        )
        theme_btn.pack(side="right", padx=10)

        # Main content (3-column layout)
        content = ctk.CTkFrame(self, corner_radius=0)
        content.pack(fill="both", expand=True)

        # Left: Folder sidebar
        sidebar = FolderSidebar(content, outlook_connector=None, width=200)
        sidebar.pack(side="left", fill="y")

        # Center: Email list
        email_list = EmailListView(content)
        email_list.pack(side="left", fill="both", expand=True)

        # Add demo emails
        demo_emails = [
            {
                "sender": "John Doe",
                "subject": "Important: Project deadline approaching",
                "priority": "high",
                "timestamp": "10:30 AM",
                "is_unread": True
            },
            {
                "sender": "Jane Smith",
                "subject": "Weekly team meeting notes",
                "priority": "medium",
                "timestamp": "Yesterday",
                "is_unread": False
            },
            {
                "sender": "Newsletter Bot",
                "subject": "Your weekly newsletter digest",
                "priority": "low",
                "timestamp": "2 days ago",
                "is_unread": False
            }
        ]

        for email in demo_emails:
            email_list.add_email(email)

        # Right: Analysis panel
        analysis = AnalysisPanel(content, width=400)
        analysis.pack(side="right", fill="y")

        # Show sample analysis with full details
        analysis.display_analysis({
            "priority": "high",
            "confidence": 0.92,
            "summary": "This email requires urgent attention regarding the project deadline. Action required within 24 hours. The sender is requesting immediate confirmation of resource allocation and timeline adjustments for the Q4 deliverables.",
            "tags": ["urgent", "project-deadline", "resources", "Q4"],
            "sentiment": "urgent",
            "sentiment_score": 0.88,
            "action_items": [
                "Confirm resource allocation by EOD",
                "Review timeline adjustments",
                "Schedule follow-up meeting",
                "Update project stakeholders"
            ],
            "processing_time": 1.8,
            "token_speed": 85,
            "model": "llama3:8b"
        })

        # Status bar
        status_bar = ctk.CTkFrame(self, height=30, corner_radius=0)
        status_bar.pack(fill="x", side="bottom")

        ctk.CTkLabel(
            status_bar,
            text="🟢 Ollama: Connected",
            font=("Segoe UI", 9)
        ).pack(side="left", padx=10)

        ctk.CTkLabel(
            status_bar,
            text="🟢 Outlook: Connected",
            font=("Segoe UI", 9)
        ).pack(side="left", padx=10)

        ctk.CTkLabel(
            status_bar,
            text="Demo Mode - No backend services running",
            font=("Segoe UI", 9),
            text_color="gray"
        ).pack(side="right", padx=10)

    def _toggle_theme(self):
        """Toggle between dark and light themes."""
        self.theme_mgr.toggle_theme()
        self.toast_mgr.show(
            f"Theme switched to {self.theme_mgr.get_current_theme()}",
            toast_type="info",
            duration=2000
        )


def main():
    """Run UI demo."""
    print("Starting MailMind UI Demo...")
    print("This demonstrates Story 2.3: CustomTkinter UI Framework")
    print("Features shown:")
    print("  - Main window with 3-panel layout")
    print("  - Folder sidebar")
    print("  - Email list with priority indicators")
    print("  - Analysis panel with expandable sections")
    print("  - Theme toggle (dark/light)")
    print("  - Toast notifications")
    print("\nPress Ctrl+C or close the window to exit")

    app = MailMindDemo()
    app.mainloop()


if __name__ == "__main__":
    main()
