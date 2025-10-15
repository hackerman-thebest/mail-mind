"""
Unit tests for FeatureTour component.

Tests Story 2.5 AC7: Feature tour on first run
"""

import pytest
import customtkinter as ctk
from unittest.mock import Mock

from mailmind.ui.dialogs.feature_tour import FeatureTour


@pytest.fixture
def root():
    """Create root window for tests."""
    root = ctk.CTk()
    yield root
    root.destroy()


class TestFeatureTourInitialization:
    """Test FeatureTour initialization."""

    def test_initialization_basic(self, root):
        """Test tour initializes with required properties."""
        tour = FeatureTour(root)

        assert tour.on_complete_callback is None
        assert tour.current_slide == 0
        assert tour.total_slides == 4
        assert len(tour.slides) == 4

        tour.destroy()

    def test_initialization_with_callback(self, root):
        """Test tour initializes with completion callback."""
        callback = Mock()
        tour = FeatureTour(root, on_complete=callback)

        assert tour.on_complete_callback == callback

        tour.destroy()

    def test_tour_is_modal(self, root):
        """Test tour is modal (transient and grab_set)."""
        tour = FeatureTour(root)

        # Dialog should be transient
        assert tour.transient() is not None

        tour.destroy()

    def test_window_properties(self, root):
        """Test tour window properties."""
        tour = FeatureTour(root)

        assert tour.title() == "MailMind Feature Tour"
        assert "700x500" in tour.geometry()  # May include position

        tour.destroy()


class TestFeatureSlides:
    """Test feature slide content."""

    def test_slides_count(self, root):
        """Test tour has 4 slides."""
        tour = FeatureTour(root)

        assert tour.total_slides == 4
        assert len(tour.slides) == 4

        tour.destroy()

    def test_slide_structure(self, root):
        """Test each slide has required fields."""
        tour = FeatureTour(root)

        for slide in tour.slides:
            assert "icon" in slide
            assert "title" in slide
            assert "description" in slide
            assert len(slide["icon"]) > 0
            assert len(slide["title"]) > 0
            assert len(slide["description"]) > 0

        tour.destroy()

    def test_slide_1_priority_detection(self, root):
        """Test slide 1 covers Priority Detection."""
        tour = FeatureTour(root)

        slide = tour.slides[0]
        assert "Priority" in slide["title"]
        assert "priority" in slide["description"].lower()

        tour.destroy()

    def test_slide_2_response_assistant(self, root):
        """Test slide 2 covers Response Assistant."""
        tour = FeatureTour(root)

        slide = tour.slides[1]
        assert "Response" in slide["title"]
        assert "response" in slide["description"].lower()

        tour.destroy()

    def test_slide_3_database_storage(self, root):
        """Test slide 3 covers Database Storage."""
        tour = FeatureTour(root)

        slide = tour.slides[2]
        assert "Storage" in slide["title"]
        assert "local" in slide["description"].lower()

        tour.destroy()

    def test_slide_4_performance_monitoring(self, root):
        """Test slide 4 covers Performance Monitoring."""
        tour = FeatureTour(root)

        slide = tour.slides[3]
        assert "Performance" in slide["title"]
        assert "performance" in slide["description"].lower()

        tour.destroy()


class TestSlideNavigation:
    """Test slide navigation."""

    def test_initial_slide(self, root):
        """Test tour starts at slide 0."""
        tour = FeatureTour(root)

        assert tour.current_slide == 0

        tour.destroy()

    def test_show_slide_updates_current_slide(self, root):
        """Test _show_slide updates current_slide."""
        tour = FeatureTour(root)

        tour._show_slide(2)
        assert tour.current_slide == 2

        tour.destroy()

    def test_next_button_advances_slide(self, root):
        """Test Next button advances to next slide."""
        tour = FeatureTour(root)

        tour._show_slide(0)
        tour._on_next_clicked()

        assert tour.current_slide == 1

        tour.destroy()

    def test_previous_button_goes_to_previous_slide(self, root):
        """Test Previous button goes to previous slide."""
        tour = FeatureTour(root)

        tour._show_slide(2)
        tour._on_previous_clicked()

        assert tour.current_slide == 1

        tour.destroy()

    def test_previous_button_disabled_on_first_slide(self, root):
        """Test Previous button is disabled on first slide."""
        tour = FeatureTour(root)

        tour._show_slide(0)
        # Previous button should be disabled, calling it shouldn't change slide
        tour._on_previous_clicked()

        assert tour.current_slide == 0

        tour.destroy()

    def test_next_button_completes_on_last_slide(self, root):
        """Test Next button completes tour on last slide."""
        callback = Mock()
        tour = FeatureTour(root, on_complete=callback)

        tour._show_slide(3)  # Last slide
        tour._on_next_clicked()

        # Should have called completion callback
        callback.assert_called_once()

        # Note: tour.destroy() called by _complete_tour


class TestNavigationButtons:
    """Test navigation button states."""

    def test_previous_button_disabled_on_first_slide(self, root):
        """Test Previous button is disabled on first slide."""
        tour = FeatureTour(root)

        tour._show_slide(0)
        tour._update_navigation_buttons()

        # Previous button should be disabled
        assert tour.prev_btn.cget("state") == "disabled"

        tour.destroy()

    def test_previous_button_enabled_on_other_slides(self, root):
        """Test Previous button is enabled on slides 2-4."""
        tour = FeatureTour(root)

        for slide_num in range(1, 4):
            tour._show_slide(slide_num)
            tour._update_navigation_buttons()

            assert tour.prev_btn.cget("state") == "normal"

        tour.destroy()

    def test_next_button_changes_to_finish(self, root):
        """Test Next button changes to Finish on last slide."""
        tour = FeatureTour(root)

        tour._show_slide(3)  # Last slide
        tour._update_navigation_buttons()

        assert tour.next_btn.cget("text") == "Finish"

        tour.destroy()

    def test_next_button_text_on_other_slides(self, root):
        """Test Next button says Next on slides 1-3."""
        tour = FeatureTour(root)

        for slide_num in range(0, 3):
            tour._show_slide(slide_num)
            tour._update_navigation_buttons()

            assert tour.next_btn.cget("text") == "Next"

        tour.destroy()

    def test_skip_button_hidden_on_last_slide(self, root):
        """Test Skip button is hidden on last slide."""
        tour = FeatureTour(root)

        tour._show_slide(3)  # Last slide
        tour._update_navigation_buttons()

        # Skip button should not be mapped
        assert not tour.skip_btn.winfo_ismapped()

        tour.destroy()

    def test_skip_button_visible_on_other_slides(self, root):
        """Test Skip button is visible on slides 1-3."""
        tour = FeatureTour(root)

        for slide_num in range(0, 3):
            tour._show_slide(slide_num)
            tour._update_navigation_buttons()

            assert tour.skip_btn.winfo_ismapped()

        tour.destroy()


class TestSkipFunctionality:
    """Test Skip Tour functionality."""

    def test_skip_button_closes_tour(self, root):
        """Test Skip button closes tour."""
        tour = FeatureTour(root)

        tour._on_skip_clicked()

        # Note: tour.destroy() called by _on_skip_clicked

    def test_skip_button_calls_callback(self, root):
        """Test Skip button calls completion callback."""
        callback = Mock()
        tour = FeatureTour(root, on_complete=callback)

        tour._on_skip_clicked()

        callback.assert_called_once()

        # Note: tour.destroy() called by _on_skip_clicked

    def test_skip_from_any_slide(self, root):
        """Test Skip button works from any slide."""
        for slide_num in range(0, 3):
            callback = Mock()
            tour = FeatureTour(root, on_complete=callback)

            tour._show_slide(slide_num)
            tour._on_skip_clicked()

            callback.assert_called_once()

            # Note: tour.destroy() called by _on_skip_clicked


class TestCompletionFunctionality:
    """Test tour completion."""

    def test_complete_tour_calls_callback(self, root):
        """Test completing tour calls callback."""
        callback = Mock()
        tour = FeatureTour(root, on_complete=callback)

        tour._complete_tour()

        callback.assert_called_once()

        # Note: tour.destroy() called by _complete_tour

    def test_complete_tour_without_callback(self, root):
        """Test completing tour without callback doesn't crash."""
        tour = FeatureTour(root)

        # Should not crash
        tour._complete_tour()

        # Note: tour.destroy() called by _complete_tour


class TestSlideIndicator:
    """Test slide indicator."""

    def test_slide_indicator_updates(self, root):
        """Test slide indicator updates correctly."""
        tour = FeatureTour(root)

        for slide_num in range(0, 4):
            tour._show_slide(slide_num)
            expected_text = f"{slide_num + 1} / 4"
            assert tour.slide_indicator.cget("text") == expected_text

        tour.destroy()

    def test_slide_indicator_format(self, root):
        """Test slide indicator has correct format."""
        tour = FeatureTour(root)

        # Should be "1 / 4" format
        indicator_text = tour.slide_indicator.cget("text")
        assert "/" in indicator_text
        assert "1" in indicator_text
        assert "4" in indicator_text

        tour.destroy()


class TestSlideContent:
    """Test slide content display."""

    def test_slide_shows_icon(self, root):
        """Test slide displays icon."""
        tour = FeatureTour(root)

        for slide_num in range(0, 4):
            tour._show_slide(slide_num)
            # Check that content frame has children (icon, title, description)
            assert len(tour.content_frame.winfo_children()) > 0

        tour.destroy()

    def test_slide_clears_previous_content(self, root):
        """Test showing new slide clears previous content."""
        tour = FeatureTour(root)

        tour._show_slide(0)
        children_count_1 = len(tour.content_frame.winfo_children())

        tour._show_slide(1)
        children_count_2 = len(tour.content_frame.winfo_children())

        # Should have similar number of children (replaced, not added)
        assert abs(children_count_1 - children_count_2) <= 1

        tour.destroy()


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_navigate_all_slides_sequentially(self, root):
        """Test navigating through all slides sequentially."""
        tour = FeatureTour(root)

        # Start at slide 0
        assert tour.current_slide == 0

        # Navigate forward through all slides
        for expected_slide in range(1, 4):
            tour._on_next_clicked()
            assert tour.current_slide == expected_slide

        # Navigate back through all slides
        for expected_slide in range(2, -1, -1):
            tour._on_previous_clicked()
            assert tour.current_slide == expected_slide

        tour.destroy()

    def test_complete_tour_from_each_slide_via_skip(self, root):
        """Test completing tour via Skip from each slide."""
        for start_slide in range(0, 3):
            callback = Mock()
            tour = FeatureTour(root, on_complete=callback)

            tour._show_slide(start_slide)
            tour._on_skip_clicked()

            callback.assert_called_once()

            # Note: tour.destroy() called by _on_skip_clicked

    def test_multiple_navigation_operations(self, root):
        """Test multiple navigation operations."""
        tour = FeatureTour(root)

        # Complex navigation sequence
        tour._on_next_clicked()  # 0 -> 1
        assert tour.current_slide == 1

        tour._on_next_clicked()  # 1 -> 2
        assert tour.current_slide == 2

        tour._on_previous_clicked()  # 2 -> 1
        assert tour.current_slide == 1

        tour._on_next_clicked()  # 1 -> 2
        assert tour.current_slide == 2

        tour._on_next_clicked()  # 2 -> 3
        assert tour.current_slide == 3

        tour.destroy()

    def test_slide_content_not_empty(self, root):
        """Test all slides have non-empty content."""
        tour = FeatureTour(root)

        for slide_num in range(0, 4):
            slide = tour.slides[slide_num]

            assert len(slide["icon"]) > 0
            assert len(slide["title"]) > 0
            assert len(slide["description"]) > 50  # Substantial description

        tour.destroy()

    def test_tour_can_be_replayed(self, root):
        """Test tour can be instantiated multiple times (replay)."""
        # First tour
        callback1 = Mock()
        tour1 = FeatureTour(root, on_complete=callback1)
        tour1._complete_tour()

        callback1.assert_called_once()

        # Second tour (replay)
        callback2 = Mock()
        tour2 = FeatureTour(root, on_complete=callback2)

        assert tour2.current_slide == 0
        assert tour2.total_slides == 4

        tour2.destroy()
