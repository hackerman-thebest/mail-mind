"""
Feature Tour

Implements Story 2.5 AC7: Feature tour on first run
- Brief feature tour slides shown after wizard
- 4 key features: Priority Detection, Response Assistant, Database Storage, Performance Monitoring
- Skip and Next navigation
- Can be replayed from Help menu
"""

import logging
import customtkinter as ctk
from typing import Optional, Callable, List, Dict

logger = logging.getLogger(__name__)


class FeatureTour(ctk.CTkToplevel):
    """
    Feature tour dialog with slides explaining key MailMind features.

    Features:
    - 4 slides covering main features
    - Skip and Next navigation
    - Clean visual presentation
    - Can be launched anytime from Help menu
    """

    def __init__(
        self,
        parent,
        on_complete: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        """
        Initialize FeatureTour.

        Args:
            parent: Parent window
            on_complete: Callback when tour completes
        """
        super().__init__(parent, **kwargs)

        self.on_complete_callback = on_complete
        self.current_slide = 0
        self.total_slides = 4

        # Configure window
        self.title("MailMind Feature Tour")
        self.geometry("700x500")
        self.resizable(False, False)

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Feature slides data
        self.slides = self._get_feature_slides()

        # Create UI
        self._create_widgets()

        # Show first slide
        self._show_slide(0)

        logger.debug("FeatureTour initialized")

    def _get_feature_slides(self) -> List[Dict[str, str]]:
        """Get feature slide data."""
        return [
            {
                "icon": "🎯",
                "title": "Smart Priority Detection",
                "description": """MailMind automatically analyzes your emails and identifies urgent messages that need your attention.

Key Features:
  • AI-powered priority classification
  • Context-aware urgency detection
  • Learns from your email patterns
  • Highlights time-sensitive requests
  • Filters out noise and low-priority emails

You'll see priority indicators next to each email, helping you focus on what matters most."""
            },
            {
                "icon": "✨",
                "title": "AI Response Assistant",
                "description": """Generate professional email responses with a single click using local AI processing.

Key Features:
  • Context-aware response generation
  • Multiple tone options (Professional, Friendly, Formal, Casual)
  • Adjustable response length (Brief, Standard, Detailed)
  • Learns your writing style
  • Fully editable before sending

The AI Assistant understands email context and generates appropriate responses that match your communication style."""
            },
            {
                "icon": "💾",
                "title": "Secure Local Storage",
                "description": """All your email data is processed and stored entirely on your local machine - no cloud required.

Key Features:
  • 100% local processing - your data never leaves your computer
  • Encrypted SQLite database
  • Fast full-text search
  • Email indexing for instant access
  • No internet required for analysis

Your privacy is our priority. MailMind works completely offline, ensuring your sensitive email data stays private."""
            },
            {
                "icon": "⚡",
                "title": "Performance Monitoring",
                "description": """MailMind continuously monitors performance and adapts to your hardware capabilities.

Key Features:
  • Real-time performance metrics
  • Hardware-optimized AI models
  • Adaptive batch processing
  • Resource usage monitoring
  • Performance recommendations

The system automatically adjusts processing based on your hardware tier, ensuring optimal performance whether you have a basic laptop or a powerful workstation."""
            }
        ]

    def _create_widgets(self):
        """Create tour widgets."""
        # Content frame (swappable per slide)
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=40, pady=30)

        # Slide indicator
        self.slide_indicator = ctk.CTkLabel(
            self,
            text=f"{self.current_slide + 1} / {self.total_slides}",
            font=("Segoe UI", 11),
            text_color="gray"
        )
        self.slide_indicator.pack(pady=5)

        # Navigation buttons
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x", padx=30, pady=20)

        self.skip_btn = ctk.CTkButton(
            nav_frame,
            text="Skip Tour",
            command=self._on_skip_clicked,
            width=100,
            fg_color="transparent",
            border_width=1
        )
        self.skip_btn.pack(side="left", padx=5)

        self.prev_btn = ctk.CTkButton(
            nav_frame,
            text="Previous",
            command=self._on_previous_clicked,
            width=100,
            fg_color="transparent",
            border_width=1
        )
        self.prev_btn.pack(side="left", padx=5)

        self.next_btn = ctk.CTkButton(
            nav_frame,
            text="Next",
            command=self._on_next_clicked,
            width=100
        )
        self.next_btn.pack(side="right", padx=5)

    def _show_slide(self, slide_number: int):
        """
        Show specific slide.

        Args:
            slide_number: Slide number (0-indexed)
        """
        self.current_slide = slide_number
        self.slide_indicator.configure(text=f"{self.current_slide + 1} / {self.total_slides}")

        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Get slide data
        slide = self.slides[slide_number]

        # Icon
        icon_label = ctk.CTkLabel(
            self.content_frame,
            text=slide["icon"],
            font=("Segoe UI", 48)
        )
        icon_label.pack(pady=15)

        # Title
        title_label = ctk.CTkLabel(
            self.content_frame,
            text=slide["title"],
            font=("Segoe UI", 20, "bold")
        )
        title_label.pack(pady=10)

        # Description
        desc_textbox = ctk.CTkTextbox(
            self.content_frame,
            height=280,
            wrap="word",
            font=("Segoe UI", 12)
        )
        desc_textbox.pack(fill="both", expand=True, pady=10)
        desc_textbox.insert("1.0", slide["description"])
        desc_textbox.configure(state="disabled")

        # Update button states
        self._update_navigation_buttons()

        logger.debug(f"Showing feature tour slide {slide_number + 1}")

    def _update_navigation_buttons(self):
        """Update navigation button states."""
        # Previous button (disabled on first slide)
        self.prev_btn.configure(state="normal" if self.current_slide > 0 else "disabled")

        # Next/Finish button
        if self.current_slide == self.total_slides - 1:
            self.next_btn.configure(text="Finish")
        else:
            self.next_btn.configure(text="Next")

        # Hide skip button on last slide
        if self.current_slide == self.total_slides - 1:
            self.skip_btn.pack_forget()
        else:
            if not self.skip_btn.winfo_ismapped():
                self.skip_btn.pack(side="left", padx=5)

    def _on_previous_clicked(self):
        """Handle Previous button click."""
        if self.current_slide > 0:
            self._show_slide(self.current_slide - 1)

    def _on_next_clicked(self):
        """Handle Next button click."""
        if self.current_slide < self.total_slides - 1:
            self._show_slide(self.current_slide + 1)
        else:
            # Finish tour
            self._complete_tour()

    def _on_skip_clicked(self):
        """Handle Skip Tour button click."""
        logger.info("Feature tour skipped")
        self.destroy()

        # Call completion callback
        if self.on_complete_callback:
            self.on_complete_callback()

    def _complete_tour(self):
        """Complete tour."""
        logger.info("Feature tour completed")
        self.destroy()

        # Call completion callback
        if self.on_complete_callback:
            self.on_complete_callback()
