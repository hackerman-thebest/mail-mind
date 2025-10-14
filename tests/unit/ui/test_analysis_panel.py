"""
Unit tests for AnalysisPanel component.

Tests Story 2.3 AC4: Analysis panel with progressive disclosure
"""

import pytest
import customtkinter as ctk
from unittest.mock import Mock, patch

from mailmind.ui.components.analysis_panel import AnalysisPanel


@pytest.fixture
def root():
    """Create root window for tests."""
    root = ctk.CTk()
    yield root
    root.destroy()


@pytest.fixture
def panel(root):
    """Create AnalysisPanel for tests."""
    return AnalysisPanel(root)


@pytest.fixture
def sample_analysis():
    """Create sample analysis data."""
    return {
        "priority": "high",
        "confidence": 0.92,
        "summary": "This is a detailed summary of the email content that needs action.",
        "tags": ["urgent", "action-required", "meeting", "deadline", "project-alpha"],
        "sentiment": "urgent",
        "sentiment_score": 0.88,
        "action_items": [
            "Review attached proposal by Friday",
            "Schedule meeting with stakeholders",
            "Prepare quarterly report"
        ],
        "processing_time": 1.85,
        "token_speed": 95,
        "model": "llama3:8b"
    }


class TestAnalysisPanelInitialization:
    """Test AnalysisPanel initialization."""

    def test_initialization(self, root):
        """Test panel initializes correctly."""
        panel = AnalysisPanel(root)

        assert panel.current_analysis is None
        assert panel.is_loading is False
        assert panel.has_error is False
        assert panel.error_message == ""
        assert panel.on_analyze_clicked_callback is None

    def test_initialization_with_callback(self, root):
        """Test panel initializes with callback."""
        callback = Mock()
        panel = AnalysisPanel(root, on_analyze_clicked=callback)

        assert panel.on_analyze_clicked_callback == callback

    def test_sections_initialized(self, panel):
        """Test all 5 sections are initialized."""
        expected_sections = ["summary", "tags", "sentiment", "action_items", "performance"]

        assert len(panel.sections) == 5
        for section_key in expected_sections:
            assert section_key in panel.sections
            assert panel.sections[section_key]["frame"] is not None
            assert panel.sections[section_key]["header_btn"] is not None
            assert panel.sections[section_key]["content_frame"] is None  # Initially collapsed

    def test_all_sections_initially_collapsed(self, panel):
        """Test all sections start collapsed."""
        for section_key, is_expanded in panel.expanded_sections.items():
            assert is_expanded is False


class TestAnalysisPanelDisplay:
    """Test analysis display functionality."""

    def test_display_analysis_high_priority(self, panel, sample_analysis):
        """Test displaying high priority analysis."""
        panel.display_analysis(sample_analysis)

        assert panel.current_analysis == sample_analysis
        assert panel.is_loading is False
        assert panel.has_error is False

        # Check priority display
        priority_text = panel.priority_label.cget("text")
        assert "🔴" in priority_text
        assert "High Priority" in priority_text
        assert "92%" in priority_text

    def test_display_analysis_medium_priority(self, panel):
        """Test displaying medium priority analysis."""
        analysis = {
            "priority": "medium",
            "confidence": 0.75,
            "summary": "Medium priority email"
        }

        panel.display_analysis(analysis)

        priority_text = panel.priority_label.cget("text")
        assert "🟡" in priority_text
        assert "Medium Priority" in priority_text
        assert "75%" in priority_text

    def test_display_analysis_low_priority(self, panel):
        """Test displaying low priority analysis."""
        analysis = {
            "priority": "low",
            "confidence": 0.60,
            "summary": "Low priority email"
        }

        panel.display_analysis(analysis)

        priority_text = panel.priority_label.cget("text")
        assert "🔵" in priority_text
        assert "Low Priority" in priority_text
        assert "60%" in priority_text

    def test_display_analysis_truncates_long_summary(self, panel):
        """Test summary is truncated if too long."""
        long_summary = "A" * 200  # 200 characters
        analysis = {
            "priority": "high",
            "confidence": 0.8,
            "summary": long_summary
        }

        panel.display_analysis(analysis)

        summary_text = panel.summary_label.cget("text")
        assert len(summary_text) <= 154  # 150 + "..."
        assert summary_text.endswith("...")

    def test_display_analysis_short_summary_not_truncated(self, panel):
        """Test short summary is not truncated."""
        short_summary = "Short email summary"
        analysis = {
            "priority": "high",
            "confidence": 0.8,
            "summary": short_summary
        }

        panel.display_analysis(analysis)

        summary_text = panel.summary_label.cget("text")
        assert summary_text == short_summary
        assert not summary_text.endswith("...")

    def test_display_analysis_hides_analyze_button(self, panel, sample_analysis):
        """Test analyze button is hidden when analysis is displayed."""
        # Initially visible (has geometry manager)
        assert panel.analyze_btn.winfo_manager() == 'pack'

        panel.display_analysis(sample_analysis)

        # Should be hidden after display (no geometry manager)
        assert panel.analyze_btn.winfo_manager() == ''


class TestAnalysisPanelLoadingState:
    """Test loading state functionality."""

    def test_show_loading_default_message(self, panel):
        """Test show_loading with default message."""
        panel.show_loading()

        assert panel.is_loading is True
        assert panel.has_error is False

        status_text = panel.status_label.cget("text")
        assert "⏳" in status_text
        assert "Analyzing..." in status_text

    def test_show_loading_custom_message(self, panel):
        """Test show_loading with custom message."""
        panel.show_loading("Processing email with AI...")

        assert panel.is_loading is True

        status_text = panel.status_label.cget("text")
        assert "⏳" in status_text
        assert "Processing email with AI..." in status_text

    def test_show_loading_hides_quick_view(self, panel):
        """Test loading state hides quick view."""
        # Initially visible (has geometry manager)
        assert panel.quick_view_frame.winfo_manager() == 'pack'

        panel.show_loading()

        # Should be hidden during loading (no geometry manager)
        assert panel.quick_view_frame.winfo_manager() == ''


class TestAnalysisPanelErrorState:
    """Test error state functionality."""

    def test_show_error(self, panel):
        """Test show_error displays error message."""
        panel.show_error("Failed to connect to Ollama")

        assert panel.is_loading is False
        assert panel.has_error is True
        assert panel.error_message == "Failed to connect to Ollama"

        status_text = panel.status_label.cget("text")
        assert "❌" in status_text
        assert "Failed to connect to Ollama" in status_text

    def test_show_error_hides_quick_view(self, panel):
        """Test error state hides quick view."""
        panel.show_error("Error occurred")

        assert not panel.quick_view_frame.winfo_ismapped()

    def test_error_state_color(self, panel):
        """Test error message has red color."""
        panel.show_error("Error message")

        text_color = panel.status_label.cget("text_color")
        assert text_color == "#F44336"  # Red color


class TestAnalysisPanelClear:
    """Test clear functionality."""

    def test_clear_resets_state(self, panel, sample_analysis):
        """Test clear resets panel state."""
        # First display analysis
        panel.display_analysis(sample_analysis)
        assert panel.current_analysis is not None

        # Then clear
        panel.clear()

        assert panel.current_analysis is None
        assert panel.is_loading is False
        assert panel.has_error is False

    def test_clear_resets_labels(self, panel, sample_analysis):
        """Test clear resets label text."""
        panel.display_analysis(sample_analysis)

        panel.clear()

        assert panel.priority_label.cget("text") == "Priority: N/A"
        assert panel.summary_label.cget("text") == "Select an email to see analysis"

    def test_clear_shows_analyze_button(self, panel, sample_analysis):
        """Test clear shows analyze button again."""
        panel.display_analysis(sample_analysis)
        assert panel.analyze_btn.winfo_manager() == ''

        panel.clear()

        assert panel.analyze_btn.winfo_manager() == 'pack'

    def test_clear_collapses_all_sections(self, panel, sample_analysis):
        """Test clear collapses all expanded sections."""
        panel.display_analysis(sample_analysis)

        # Expand a section
        section_key = "summary"
        section = panel.sections[section_key]
        panel._toggle_section(section_key, section["frame"], section["header_btn"], section["title"])
        assert panel.expanded_sections[section_key] is True

        # Clear
        panel.clear()

        # All sections should be collapsed
        for key, is_expanded in panel.expanded_sections.items():
            assert is_expanded is False


class TestAnalysisPanelSectionToggle:
    """Test section expand/collapse functionality."""

    def test_toggle_section_expand(self, panel, sample_analysis):
        """Test expanding a section."""
        panel.display_analysis(sample_analysis)

        section_key = "summary"
        section = panel.sections[section_key]

        # Initially collapsed
        assert panel.expanded_sections[section_key] is False
        assert section["content_frame"] is None

        # Expand
        panel._toggle_section(section_key, section["frame"], section["header_btn"], section["title"])

        # Should be expanded
        assert panel.expanded_sections[section_key] is True
        assert section["content_frame"] is not None
        assert "▼" in section["header_btn"].cget("text")

    def test_toggle_section_collapse(self, panel, sample_analysis):
        """Test collapsing a section."""
        panel.display_analysis(sample_analysis)

        section_key = "tags"
        section = panel.sections[section_key]

        # Expand first
        panel._toggle_section(section_key, section["frame"], section["header_btn"], section["title"])
        assert panel.expanded_sections[section_key] is True

        # Collapse
        panel._toggle_section(section_key, section["frame"], section["header_btn"], section["title"])

        # Should be collapsed
        assert panel.expanded_sections[section_key] is False
        assert section["content_frame"] is None
        assert "▶" in section["header_btn"].cget("text")

    def test_toggle_multiple_sections(self, panel, sample_analysis):
        """Test expanding multiple sections simultaneously."""
        panel.display_analysis(sample_analysis)

        # Expand summary and tags
        for section_key in ["summary", "tags"]:
            section = panel.sections[section_key]
            panel._toggle_section(section_key, section["frame"], section["header_btn"], section["title"])

        # Both should be expanded
        assert panel.expanded_sections["summary"] is True
        assert panel.expanded_sections["tags"] is True
        assert panel.sections["summary"]["content_frame"] is not None
        assert panel.sections["tags"]["content_frame"] is not None


class TestAnalysisPanelSectionContent:
    """Test section content creation."""

    def test_summary_section_content(self, panel, sample_analysis):
        """Test summary section displays full text."""
        panel.display_analysis(sample_analysis)

        section_key = "summary"
        section = panel.sections[section_key]
        panel._toggle_section(section_key, section["frame"], section["header_btn"], section["title"])

        # Content frame should exist
        content_frame = section["content_frame"]
        assert content_frame is not None

    def test_tags_section_content(self, panel, sample_analysis):
        """Test tags section displays tags."""
        panel.display_analysis(sample_analysis)

        section_key = "tags"
        section = panel.sections[section_key]
        panel._toggle_section(section_key, section["frame"], section["header_btn"], section["title"])

        assert section["content_frame"] is not None

    def test_tags_section_empty_tags(self, panel):
        """Test tags section with no tags."""
        analysis = {
            "priority": "low",
            "confidence": 0.5,
            "summary": "Test",
            "tags": []
        }

        panel.display_analysis(analysis)
        section_key = "tags"
        section = panel.sections[section_key]
        panel._toggle_section(section_key, section["frame"], section["header_btn"], section["title"])

        # Should show "No tags identified"
        assert section["content_frame"] is not None

    def test_sentiment_section_positive(self, panel):
        """Test sentiment section with positive sentiment."""
        analysis = {
            "priority": "low",
            "confidence": 0.5,
            "summary": "Test",
            "sentiment": "positive",
            "sentiment_score": 0.85
        }

        panel.display_analysis(analysis)
        section_key = "sentiment"
        section = panel.sections[section_key]
        panel._toggle_section(section_key, section["frame"], section["header_btn"], section["title"])

        assert section["content_frame"] is not None

    def test_sentiment_section_negative(self, panel):
        """Test sentiment section with negative sentiment."""
        analysis = {
            "priority": "medium",
            "confidence": 0.7,
            "summary": "Test",
            "sentiment": "negative",
            "sentiment_score": 0.75
        }

        panel.display_analysis(analysis)
        section_key = "sentiment"
        section = panel.sections[section_key]
        panel._toggle_section(section_key, section["frame"], section["header_btn"], section["title"])

        assert section["content_frame"] is not None

    def test_action_items_section_content(self, panel, sample_analysis):
        """Test action items section displays checkboxes."""
        panel.display_analysis(sample_analysis)

        section_key = "action_items"
        section = panel.sections[section_key]
        panel._toggle_section(section_key, section["frame"], section["header_btn"], section["title"])

        assert section["content_frame"] is not None

    def test_action_items_section_empty(self, panel):
        """Test action items section with no items."""
        analysis = {
            "priority": "low",
            "confidence": 0.5,
            "summary": "Test",
            "action_items": []
        }

        panel.display_analysis(analysis)
        section_key = "action_items"
        section = panel.sections[section_key]
        panel._toggle_section(section_key, section["frame"], section["header_btn"], section["title"])

        # Should show "No action items identified"
        assert section["content_frame"] is not None

    def test_performance_section_content(self, panel, sample_analysis):
        """Test performance section displays metrics."""
        panel.display_analysis(sample_analysis)

        section_key = "performance"
        section = panel.sections[section_key]
        panel._toggle_section(section_key, section["frame"], section["header_btn"], section["title"])

        assert section["content_frame"] is not None


class TestAnalysisPanelCallbacks:
    """Test callback functionality."""

    def test_analyze_button_callback(self, root):
        """Test analyze button triggers callback."""
        callback = Mock()
        panel = AnalysisPanel(root, on_analyze_clicked=callback)

        # Click analyze button
        panel._on_analyze_clicked()

        callback.assert_called_once()

    def test_analyze_button_no_callback(self, panel):
        """Test analyze button with no callback doesn't crash."""
        # Should not crash
        panel._on_analyze_clicked()

    def test_retry_button_callback(self, root):
        """Test retry button in error state triggers callback."""
        callback = Mock()
        panel = AnalysisPanel(root, on_analyze_clicked=callback)

        # Show error (which creates retry button)
        panel.show_error("Test error")

        # Click retry via callback
        panel._on_analyze_clicked()

        callback.assert_called_once()


class TestAnalysisPanelEdgeCases:
    """Test edge cases and error handling."""

    def test_display_analysis_missing_fields(self, panel):
        """Test display analysis with missing fields."""
        minimal_analysis = {
            "priority": "medium"
            # Missing: confidence, summary, tags, etc.
        }

        # Should not crash
        panel.display_analysis(minimal_analysis)

        assert panel.current_analysis == minimal_analysis

    def test_display_analysis_empty_dict(self, panel):
        """Test display analysis with empty dict."""
        panel.display_analysis({})

        assert panel.current_analysis == {}
        # Should use defaults
        assert "N/A" in panel.priority_label.cget("text") or "🟡" in panel.priority_label.cget("text")

    def test_section_content_no_analysis(self, panel):
        """Test creating section content when no analysis exists."""
        # Don't set current_analysis
        section_key = "summary"
        section = panel.sections[section_key]

        # Try to expand section without analysis
        panel._toggle_section(section_key, section["frame"], section["header_btn"], section["title"])

        # Should show "No analysis data available"
        assert section["content_frame"] is not None

    def test_unknown_sentiment(self, panel):
        """Test sentiment section with unknown sentiment type."""
        analysis = {
            "priority": "low",
            "confidence": 0.5,
            "summary": "Test",
            "sentiment": "unknown_sentiment_type",
            "sentiment_score": 0.5
        }

        # Should not crash, should use default icon
        panel.display_analysis(analysis)
        section_key = "sentiment"
        section = panel.sections[section_key]
        panel._toggle_section(section_key, section["frame"], section["header_btn"], section["title"])

        assert section["content_frame"] is not None
