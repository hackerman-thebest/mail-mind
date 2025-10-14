"""
Analysis Panel Component

Implements Story 2.3 AC4: Analysis panel with progressive disclosure
- Quick view (priority, summary)
- Expandable sections (tags, sentiment, action items, performance)
- Loading states
- Error handling
"""

import logging
import customtkinter as ctk
from typing import Optional, Dict, List, Callable

logger = logging.getLogger(__name__)


class AnalysisPanel(ctk.CTkScrollableFrame):
    """
    Analysis panel with progressive disclosure of AI analysis results.

    Features:
    - Quick view (priority + summary)
    - Expandable sections (Summary, Tags, Sentiment, Action Items, Performance)
    - Smooth expand/collapse animations
    - Loading indicators
    - Error states
    - Integration with EmailAnalysisEngine
    """

    def __init__(
        self,
        master,
        on_analyze_clicked: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        """
        Initialize AnalysisPanel.

        Args:
            master: Parent widget
            on_analyze_clicked: Callback when Analyze Now button is clicked
        """
        super().__init__(master, **kwargs)

        self.current_analysis: Optional[Dict] = None
        self.is_loading = False
        self.has_error = False
        self.error_message = ""

        self.on_analyze_clicked_callback = on_analyze_clicked

        # Section state tracking
        self.expanded_sections = {
            "summary": False,
            "tags": False,
            "sentiment": False,
            "action_items": False,
            "performance": False
        }

        # Create UI
        self._create_widgets()

        logger.debug("AnalysisPanel initialized")

    def _create_widgets(self):
        """Create panel widgets."""
        # Header
        header = ctk.CTkLabel(
            self,
            text="Email Analysis",
            font=("Segoe UI", 14, "bold")
        )
        header.pack(pady=10, padx=10, anchor="w")

        # Quick view frame
        self.quick_view_frame = ctk.CTkFrame(self)
        self.quick_view_frame.pack(fill="x", padx=10, pady=5)

        # Priority display
        self.priority_label = ctk.CTkLabel(
            self.quick_view_frame,
            text="Priority: N/A",
            font=("Segoe UI", 12)
        )
        self.priority_label.pack(pady=5, padx=10, anchor="w")

        # Summary display (one-line, truncated)
        self.summary_label = ctk.CTkLabel(
            self.quick_view_frame,
            text="Select an email to see analysis",
            font=("Segoe UI", 10),
            wraplength=350,
            justify="left"
        )
        self.summary_label.pack(pady=5, padx=10, anchor="w")

        # Analyze button
        self.analyze_btn = ctk.CTkButton(
            self.quick_view_frame,
            text="Analyze Now",
            command=self._on_analyze_clicked
        )
        self.analyze_btn.pack(pady=10, padx=10)

        # Loading/Error frame
        self.status_frame = ctk.CTkFrame(self)
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=("Segoe UI", 10),
            text_color="gray"
        )

        # Expandable sections container
        self.sections_container = ctk.CTkFrame(self, fg_color="transparent")
        self.sections_container.pack(fill="both", expand=True, padx=10, pady=5)

        # Create expandable sections
        self.sections = {}
        self._create_expandable_section("Summary", "summary")
        self._create_expandable_section("Tags", "tags")
        self._create_expandable_section("Sentiment", "sentiment")
        self._create_expandable_section("Action Items", "action_items")
        self._create_expandable_section("Performance", "performance")

    def _create_expandable_section(self, title: str, section_key: str):
        """Create expandable section."""
        section_frame = ctk.CTkFrame(self.sections_container)
        section_frame.pack(fill="x", pady=2)

        # Header button (click to expand/collapse)
        header_btn = ctk.CTkButton(
            section_frame,
            text=f"▶ {title}",
            anchor="w",
            fg_color="transparent",
            hover_color=("gray70", "gray30"),
            command=lambda: self._toggle_section(section_key, section_frame, header_btn, title)
        )
        header_btn.pack(fill="x")

        # Store references
        self.sections[section_key] = {
            "frame": section_frame,
            "header_btn": header_btn,
            "content_frame": None,
            "title": title
        }

    def _toggle_section(self, section_key: str, section_frame, header_btn, title: str):
        """Toggle section expansion."""
        section = self.sections[section_key]

        if section["content_frame"] is None:
            # Expand
            self.expanded_sections[section_key] = True
            header_btn.configure(text=f"▼ {title}")

            # Create content based on section type
            content_frame = self._create_section_content(section_key, section_frame)
            section["content_frame"] = content_frame

            if content_frame:
                content_frame.pack(fill="x", padx=10, pady=5)

            logger.debug(f"Expanded section: {section_key}")
        else:
            # Collapse
            self.expanded_sections[section_key] = False
            header_btn.configure(text=f"▶ {title}")
            section["content_frame"].destroy()
            section["content_frame"] = None

            logger.debug(f"Collapsed section: {section_key}")

    def _create_section_content(self, section_key: str, parent):
        """Create content for specific section."""
        if not self.current_analysis:
            frame = ctk.CTkFrame(parent)
            ctk.CTkLabel(
                frame,
                text="No analysis data available",
                font=("Segoe UI", 9),
                text_color="gray"
            ).pack(padx=10, pady=5)
            return frame

        if section_key == "summary":
            return self._create_summary_content(parent)
        elif section_key == "tags":
            return self._create_tags_content(parent)
        elif section_key == "sentiment":
            return self._create_sentiment_content(parent)
        elif section_key == "action_items":
            return self._create_action_items_content(parent)
        elif section_key == "performance":
            return self._create_performance_content(parent)

    def _create_summary_content(self, parent):
        """Create full summary section."""
        frame = ctk.CTkFrame(parent)

        summary = self.current_analysis.get("summary", "No summary available")

        ctk.CTkLabel(
            frame,
            text=summary,
            font=("Segoe UI", 10),
            wraplength=350,
            justify="left"
        ).pack(padx=10, pady=5, anchor="w")

        return frame

    def _create_tags_content(self, parent):
        """Create tags section with colored pills."""
        frame = ctk.CTkFrame(parent)

        tags = self.current_analysis.get("tags", [])

        if not tags:
            ctk.CTkLabel(
                frame,
                text="No tags identified",
                font=("Segoe UI", 9),
                text_color="gray"
            ).pack(padx=10, pady=5)
            return frame

        # Tags container
        tags_container = ctk.CTkFrame(frame, fg_color="transparent")
        tags_container.pack(fill="x", padx=10, pady=5)

        # Display up to 5 tags
        for tag in tags[:5]:
            tag_label = ctk.CTkLabel(
                tags_container,
                text=f"  {tag}  ",
                font=("Segoe UI", 9),
                fg_color=("gray75", "gray25"),
                corner_radius=10
            )
            tag_label.pack(side="left", padx=2, pady=2)

        return frame

    def _create_sentiment_content(self, parent):
        """Create sentiment section with icon and label."""
        frame = ctk.CTkFrame(parent)

        sentiment = self.current_analysis.get("sentiment", "neutral")
        sentiment_score = self.current_analysis.get("sentiment_score", 0.0)

        # Sentiment mapping
        sentiment_icons = {
            "positive": "😊",
            "neutral": "😐",
            "negative": "😠",
            "urgent": "⚠️"
        }

        sentiment_colors = {
            "positive": "#4CAF50",
            "neutral": "#9E9E9E",
            "negative": "#F44336",
            "urgent": "#FF9800"
        }

        icon = sentiment_icons.get(sentiment.lower(), "😐")
        color = sentiment_colors.get(sentiment.lower(), "#9E9E9E")

        sentiment_label = ctk.CTkLabel(
            frame,
            text=f"{icon} {sentiment.title()} ({sentiment_score:.0%} confidence)",
            font=("Segoe UI", 11),
            text_color=color
        )
        sentiment_label.pack(padx=10, pady=5, anchor="w")

        return frame

    def _create_action_items_content(self, parent):
        """Create action items section with checkboxes."""
        frame = ctk.CTkFrame(parent)

        action_items = self.current_analysis.get("action_items", [])

        if not action_items:
            ctk.CTkLabel(
                frame,
                text="No action items identified",
                font=("Segoe UI", 9),
                text_color="gray"
            ).pack(padx=10, pady=5)
            return frame

        # Action items list
        for item in action_items:
            item_frame = ctk.CTkFrame(frame, fg_color="transparent")
            item_frame.pack(fill="x", padx=10, pady=2)

            checkbox = ctk.CTkCheckBox(
                item_frame,
                text=item,
                font=("Segoe UI", 9)
            )
            checkbox.pack(anchor="w")

        return frame

    def _create_performance_content(self, parent):
        """Create performance metrics section."""
        frame = ctk.CTkFrame(parent)

        processing_time = self.current_analysis.get("processing_time", 0.0)
        token_speed = self.current_analysis.get("token_speed", 0)
        model = self.current_analysis.get("model", "Unknown")

        metrics_text = f"""Processing Time: {processing_time:.2f}s
Token Speed: {token_speed} tokens/sec
Model: {model}"""

        ctk.CTkLabel(
            frame,
            text=metrics_text,
            font=("Segoe UI", 9),
            text_color="gray",
            justify="left"
        ).pack(padx=10, pady=5, anchor="w")

        return frame

    def display_analysis(self, analysis: Dict):
        """
        Display analysis results.

        Args:
            analysis: Analysis dict with keys: priority, summary, tags, sentiment, action_items, etc.
        """
        self.current_analysis = analysis
        self.is_loading = False
        self.has_error = False

        # Hide loading/error
        self.status_frame.pack_forget()

        # Show quick view
        self.quick_view_frame.pack(fill="x", padx=10, pady=5)

        # Update priority
        priority = analysis.get("priority", "N/A")
        confidence = analysis.get("confidence", 0)
        priority_colors = {"high": "🔴", "medium": "🟡", "low": "🔵"}
        indicator = priority_colors.get(priority.lower(), "🟡")

        self.priority_label.configure(
            text=f"{indicator} {priority.title()} Priority - {confidence:.0%} confident"
        )

        # Update summary (truncated to 150 chars)
        summary = analysis.get("summary", "No summary available")
        truncated_summary = summary[:150] + "..." if len(summary) > 150 else summary
        self.summary_label.configure(text=truncated_summary)

        # Hide analyze button when analysis is available
        self.analyze_btn.pack_forget()

        # Show sections container
        self.sections_container.pack(fill="both", expand=True, padx=10, pady=5)

        # Refresh expanded sections
        for section_key, is_expanded in self.expanded_sections.items():
            if is_expanded:
                section = self.sections[section_key]
                # Recreate content
                if section["content_frame"]:
                    section["content_frame"].destroy()
                    content_frame = self._create_section_content(section_key, section["frame"])
                    section["content_frame"] = content_frame
                    if content_frame:
                        content_frame.pack(fill="x", padx=10, pady=5)

        logger.debug(f"Displayed analysis for email with priority: {priority}")

    def show_loading(self, message: str = "Analyzing..."):
        """Show loading state."""
        self.is_loading = True
        self.has_error = False

        # Hide quick view
        self.quick_view_frame.pack_forget()
        self.sections_container.pack_forget()

        # Show loading
        self.status_frame.pack(fill="x", padx=10, pady=20)
        self.status_label.configure(
            text=f"⏳ {message}",
            text_color=("gray50", "gray50")
        )
        self.status_label.pack(pady=10)

        logger.debug(f"Showing loading: {message}")

    def show_error(self, error_message: str):
        """Show error state."""
        self.is_loading = False
        self.has_error = True
        self.error_message = error_message

        # Hide quick view
        self.quick_view_frame.pack_forget()
        self.sections_container.pack_forget()

        # Show error
        self.status_frame.pack(fill="x", padx=10, pady=20)
        self.status_label.configure(
            text=f"❌ {error_message}",
            text_color="#F44336"
        )
        self.status_label.pack(pady=10)

        # Show retry button
        retry_btn = ctk.CTkButton(
            self.status_frame,
            text="Retry Analysis",
            command=self._on_analyze_clicked
        )
        retry_btn.pack(pady=5)

        logger.debug(f"Showing error: {error_message}")

    def clear(self):
        """Clear analysis display."""
        self.current_analysis = None
        self.is_loading = False
        self.has_error = False

        # Hide all
        self.quick_view_frame.pack_forget()
        self.status_frame.pack_forget()
        self.sections_container.pack_forget()

        # Reset to initial state
        self.quick_view_frame.pack(fill="x", padx=10, pady=5)
        self.priority_label.configure(text="Priority: N/A")
        self.summary_label.configure(text="Select an email to see analysis")
        self.analyze_btn.pack(pady=10, padx=10)

        # Collapse all sections
        for section_key in self.expanded_sections:
            self.expanded_sections[section_key] = False
            section = self.sections[section_key]
            if section["content_frame"]:
                section["content_frame"].destroy()
                section["content_frame"] = None
            section["header_btn"].configure(text=f"▶ {section['title']}")

        logger.debug("Cleared analysis panel")

    def _on_analyze_clicked(self):
        """Handle Analyze Now button click."""
        if self.on_analyze_clicked_callback:
            self.on_analyze_clicked_callback()

        logger.debug("Analyze Now clicked")
