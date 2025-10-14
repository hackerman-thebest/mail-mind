"""
Unit tests for StatusBar component.

Tests Story 2.3 AC6: Real-time performance indicators
"""

import pytest
import customtkinter as ctk
from unittest.mock import Mock, patch, call

from mailmind.ui.components.status_bar import StatusBar


@pytest.fixture
def root():
    """Create root window for tests."""
    root = ctk.CTk()
    yield root
    root.destroy()


@pytest.fixture
def status_bar(root):
    """Create StatusBar for tests."""
    return StatusBar(root)


class TestStatusBarInitialization:
    """Test StatusBar initialization."""

    def test_initialization(self, root):
        """Test status bar initializes correctly."""
        bar = StatusBar(root)

        assert bar.on_ollama_clicked_callback is None
        assert bar.on_outlook_clicked_callback is None
        assert bar.ollama_status == "disconnected"
        assert bar.outlook_status == "disconnected"
        assert bar.queue_count == 0
        assert bar.queue_total == 0
        assert bar.token_speed == 0
        assert bar.last_analysis_time == 0.0
        assert bar.auto_update_enabled is False
        assert bar.update_id is None

    def test_initialization_with_callbacks(self, root):
        """Test status bar initializes with callbacks."""
        ollama_cb = Mock()
        outlook_cb = Mock()
        bar = StatusBar(root, on_ollama_clicked=ollama_cb, on_outlook_clicked=outlook_cb)

        assert bar.on_ollama_clicked_callback == ollama_cb
        assert bar.on_outlook_clicked_callback == outlook_cb

    def test_status_icons_defined(self, status_bar):
        """Test status icons are defined."""
        assert status_bar.STATUS_ICONS["connected"] == "🟢"
        assert status_bar.STATUS_ICONS["slow"] == "🟡"
        assert status_bar.STATUS_ICONS["disconnected"] == "🔴"


class TestStatusBarOllamaStatus:
    """Test Ollama status functionality."""

    def test_set_ollama_connected(self, status_bar):
        """Test setting Ollama status to connected."""
        status_bar.set_ollama_status("connected")

        assert status_bar.ollama_status == "connected"
        text = status_bar.ollama_btn.cget("text")
        assert "🟢" in text
        assert "Connected" in text

    def test_set_ollama_slow(self, status_bar):
        """Test setting Ollama status to slow."""
        status_bar.set_ollama_status("slow")

        assert status_bar.ollama_status == "slow"
        text = status_bar.ollama_btn.cget("text")
        assert "🟡" in text
        assert "Slow" in text

    def test_set_ollama_disconnected(self, status_bar):
        """Test setting Ollama status to disconnected."""
        status_bar.set_ollama_status("disconnected")

        assert status_bar.ollama_status == "disconnected"
        text = status_bar.ollama_btn.cget("text")
        assert "🔴" in text
        assert "Disconnected" in text


class TestStatusBarOutlookStatus:
    """Test Outlook status functionality."""

    def test_set_outlook_connected(self, status_bar):
        """Test setting Outlook status to connected."""
        status_bar.set_outlook_status("connected")

        assert status_bar.outlook_status == "connected"
        text = status_bar.outlook_btn.cget("text")
        assert "🟢" in text
        assert "Connected" in text

    def test_set_outlook_slow(self, status_bar):
        """Test setting Outlook status to slow."""
        status_bar.set_outlook_status("slow")

        assert status_bar.outlook_status == "slow"
        text = status_bar.outlook_btn.cget("text")
        assert "🟡" in text
        assert "Slow" in text

    def test_set_outlook_disconnected(self, status_bar):
        """Test setting Outlook status to disconnected."""
        status_bar.set_outlook_status("disconnected")

        assert status_bar.outlook_status == "disconnected"
        text = status_bar.outlook_btn.cget("text")
        assert "🔴" in text
        assert "Disconnected" in text


class TestStatusBarQueueStatus:
    """Test processing queue status functionality."""

    def test_set_queue_status_with_items(self, status_bar):
        """Test setting queue status with items."""
        status_bar.set_queue_status(3, 10)

        assert status_bar.queue_count == 3
        assert status_bar.queue_total == 10

        text = status_bar.queue_label.cget("text")
        assert "Analyzing 3/10 emails" in text

        # Progress bar should be visible
        assert status_bar.progress_bar.winfo_manager() == 'pack'

    def test_set_queue_status_empty(self, status_bar):
        """Test setting queue status with no items."""
        # First set with items
        status_bar.set_queue_status(5, 10)

        # Then clear
        status_bar.set_queue_status(0, 0)

        assert status_bar.queue_count == 0
        assert status_bar.queue_total == 0

        text = status_bar.queue_label.cget("text")
        assert text == ""

        # Progress bar should be hidden
        assert status_bar.progress_bar.winfo_manager() == ''

    def test_set_queue_status_progress_value(self, status_bar):
        """Test queue status sets correct progress value."""
        status_bar.set_queue_status(5, 10)

        # Progress should be 50%
        progress_value = status_bar.progress_bar.get()
        assert progress_value == 0.5

    def test_set_queue_status_completed(self, status_bar):
        """Test queue status when all items complete."""
        status_bar.set_queue_status(10, 10)

        # Progress should be 100%
        progress_value = status_bar.progress_bar.get()
        assert progress_value == 1.0


class TestStatusBarTokenSpeed:
    """Test token speed functionality."""

    def test_set_token_speed_positive(self, status_bar):
        """Test setting positive token speed."""
        status_bar.set_token_speed(85)

        assert status_bar.token_speed == 85
        text = status_bar.token_speed_label.cget("text")
        assert "85 tokens/sec" in text

    def test_set_token_speed_zero(self, status_bar):
        """Test setting zero token speed."""
        # First set positive
        status_bar.set_token_speed(100)

        # Then zero
        status_bar.set_token_speed(0)

        assert status_bar.token_speed == 0
        text = status_bar.token_speed_label.cget("text")
        assert text == ""

    def test_set_token_speed_high_value(self, status_bar):
        """Test setting high token speed."""
        status_bar.set_token_speed(500)

        text = status_bar.token_speed_label.cget("text")
        assert "500 tokens/sec" in text


class TestStatusBarLastAnalysisTime:
    """Test last analysis time functionality."""

    def test_set_last_analysis_time_positive(self, status_bar):
        """Test setting positive analysis time."""
        status_bar.set_last_analysis_time(1.82)

        assert status_bar.last_analysis_time == 1.82
        text = status_bar.last_analysis_label.cget("text")
        assert "Last: 1.8s" in text

    def test_set_last_analysis_time_zero(self, status_bar):
        """Test setting zero analysis time."""
        # First set positive
        status_bar.set_last_analysis_time(2.5)

        # Then zero
        status_bar.set_last_analysis_time(0.0)

        assert status_bar.last_analysis_time == 0.0
        text = status_bar.last_analysis_label.cget("text")
        assert text == ""

    def test_set_last_analysis_time_formatting(self, status_bar):
        """Test analysis time formatting."""
        status_bar.set_last_analysis_time(0.123)
        text = status_bar.last_analysis_label.cget("text")
        assert "0.1s" in text

        status_bar.set_last_analysis_time(12.567)
        text = status_bar.last_analysis_label.cget("text")
        assert "12.6s" in text


class TestStatusBarCallbacks:
    """Test callback functionality."""

    def test_ollama_button_callback(self, root):
        """Test Ollama button triggers callback."""
        callback = Mock()
        bar = StatusBar(root, on_ollama_clicked=callback)

        # Click Ollama button
        bar._on_ollama_clicked()

        callback.assert_called_once()

    def test_ollama_button_no_callback(self, status_bar):
        """Test Ollama button with no callback doesn't crash."""
        # Should not crash
        status_bar._on_ollama_clicked()

    def test_outlook_button_callback(self, root):
        """Test Outlook button triggers callback."""
        callback = Mock()
        bar = StatusBar(root, on_outlook_clicked=callback)

        # Click Outlook button
        bar._on_outlook_clicked()

        callback.assert_called_once()

    def test_outlook_button_no_callback(self, status_bar):
        """Test Outlook button with no callback doesn't crash."""
        # Should not crash
        status_bar._on_outlook_clicked()


class TestStatusBarAutoUpdate:
    """Test auto-update functionality."""

    def test_start_auto_update(self, status_bar):
        """Test starting auto-update."""
        callback = Mock(return_value={})

        status_bar.start_auto_update(callback)

        assert status_bar.auto_update_enabled is True
        assert status_bar._update_callback == callback

    def test_auto_update_calls_callback(self, status_bar):
        """Test auto-update calls the callback."""
        callback = Mock(return_value={
            "ollama_status": "connected",
            "outlook_status": "connected",
            "queue_current": 3,
            "queue_total": 10,
            "token_speed": 95,
            "last_analysis_time": 1.5
        })

        status_bar.start_auto_update(callback)

        # Callback should have been called once (first update)
        callback.assert_called_once()

    def test_auto_update_updates_ollama_status(self, status_bar):
        """Test auto-update updates Ollama status."""
        callback = Mock(return_value={"ollama_status": "connected"})

        status_bar.start_auto_update(callback)

        assert status_bar.ollama_status == "connected"

    def test_auto_update_updates_outlook_status(self, status_bar):
        """Test auto-update updates Outlook status."""
        callback = Mock(return_value={"outlook_status": "slow"})

        status_bar.start_auto_update(callback)

        assert status_bar.outlook_status == "slow"

    def test_auto_update_updates_queue_status(self, status_bar):
        """Test auto-update updates queue status."""
        callback = Mock(return_value={"queue_current": 5, "queue_total": 15})

        status_bar.start_auto_update(callback)

        assert status_bar.queue_count == 5
        assert status_bar.queue_total == 15

    def test_auto_update_updates_token_speed(self, status_bar):
        """Test auto-update updates token speed."""
        callback = Mock(return_value={"token_speed": 120})

        status_bar.start_auto_update(callback)

        assert status_bar.token_speed == 120

    def test_auto_update_updates_last_analysis_time(self, status_bar):
        """Test auto-update updates last analysis time."""
        callback = Mock(return_value={"last_analysis_time": 2.3})

        status_bar.start_auto_update(callback)

        assert status_bar.last_analysis_time == 2.3

    def test_auto_update_handles_missing_keys(self, status_bar):
        """Test auto-update handles missing status keys."""
        callback = Mock(return_value={"ollama_status": "connected"})
        # Only provides ollama_status, missing all others

        # Should not crash
        status_bar.start_auto_update(callback)

        assert status_bar.ollama_status == "connected"

    def test_auto_update_handles_error(self, status_bar):
        """Test auto-update handles callback errors gracefully."""
        callback = Mock(side_effect=Exception("Test error"))

        # Should not crash
        status_bar.start_auto_update(callback)

        # Should still be enabled despite error
        assert status_bar.auto_update_enabled is True

    def test_stop_auto_update(self, status_bar):
        """Test stopping auto-update."""
        callback = Mock(return_value={})

        status_bar.start_auto_update(callback)
        assert status_bar.auto_update_enabled is True

        status_bar.stop_auto_update()

        assert status_bar.auto_update_enabled is False
        assert status_bar.update_id is None


class TestStatusBarClear:
    """Test clear functionality."""

    def test_clear_resets_all_indicators(self, status_bar):
        """Test clear resets all indicators to defaults."""
        # Set all indicators
        status_bar.set_ollama_status("connected")
        status_bar.set_outlook_status("connected")
        status_bar.set_queue_status(5, 10)
        status_bar.set_token_speed(100)
        status_bar.set_last_analysis_time(2.5)

        # Clear
        status_bar.clear()

        # All should be reset
        assert status_bar.ollama_status == "disconnected"
        assert status_bar.outlook_status == "disconnected"
        assert status_bar.queue_count == 0
        assert status_bar.queue_total == 0
        assert status_bar.token_speed == 0
        assert status_bar.last_analysis_time == 0.0

    def test_clear_multiple_times(self, status_bar):
        """Test clearing multiple times doesn't break state."""
        status_bar.clear()
        status_bar.clear()
        status_bar.clear()

        # Should still be in cleared state
        assert status_bar.ollama_status == "disconnected"
        assert status_bar.outlook_status == "disconnected"


class TestStatusBarEdgeCases:
    """Test edge cases and error handling."""

    def test_set_queue_with_negative_values(self, status_bar):
        """Test setting queue with negative values."""
        # Should handle gracefully (though shouldn't happen in practice)
        status_bar.set_queue_status(-1, 10)

        # Negative progress will be clamped by progress bar
        assert status_bar.queue_count == -1
        assert status_bar.queue_total == 10

    def test_set_queue_with_current_greater_than_total(self, status_bar):
        """Test setting queue with current > total."""
        status_bar.set_queue_status(15, 10)

        # Progress will be > 1.0, but CTkProgressBar clamps to 1.0
        progress_value = status_bar.progress_bar.get()
        assert progress_value == 1.0  # Clamped to max

    def test_very_high_token_speed(self, status_bar):
        """Test setting very high token speed."""
        status_bar.set_token_speed(99999)

        text = status_bar.token_speed_label.cget("text")
        assert "99999 tokens/sec" in text

    def test_very_long_analysis_time(self, status_bar):
        """Test setting very long analysis time."""
        status_bar.set_last_analysis_time(999.9)

        text = status_bar.last_analysis_label.cget("text")
        assert "999.9s" in text

    def test_auto_update_empty_dict(self, status_bar):
        """Test auto-update with empty dict."""
        callback = Mock(return_value={})

        # Should not crash
        status_bar.start_auto_update(callback)

        callback.assert_called_once()

    def test_multiple_status_changes(self, status_bar):
        """Test multiple rapid status changes."""
        # Change Ollama status multiple times
        for status in ["connected", "slow", "disconnected", "connected"]:
            status_bar.set_ollama_status(status)

        assert status_bar.ollama_status == "connected"

    def test_callbacks_both_defined(self, root):
        """Test both callbacks can be defined and work."""
        ollama_cb = Mock()
        outlook_cb = Mock()
        bar = StatusBar(root, on_ollama_clicked=ollama_cb, on_outlook_clicked=outlook_cb)

        bar._on_ollama_clicked()
        bar._on_outlook_clicked()

        ollama_cb.assert_called_once()
        outlook_cb.assert_called_once()
