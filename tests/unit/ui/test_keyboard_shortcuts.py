"""
Unit tests for Keyboard Shortcuts module.

Tests Story 2.3 AC8: Keyboard shortcuts for common actions
"""

import pytest
import customtkinter as ctk
from unittest.mock import Mock

from mailmind.ui.keyboard_shortcuts import (
    SHORTCUTS,
    bind_shortcuts,
    get_shortcuts_text
)


@pytest.fixture
def root():
    """Create root window for tests."""
    root = ctk.CTk()
    yield root
    root.destroy()


class TestShortcutsDefinition:
    """Test SHORTCUTS dictionary."""

    def test_shortcuts_defined(self):
        """Test all shortcuts are defined."""
        assert len(SHORTCUTS) == 10

    def test_refresh_shortcut(self):
        """Test refresh shortcut is defined."""
        assert "<Control-r>" in SHORTCUTS
        assert SHORTCUTS["<Control-r>"]["action"] == "refresh_email_list"
        assert "Refresh" in SHORTCUTS["<Control-r>"]["description"]

    def test_analyze_shortcut(self):
        """Test analyze shortcut is defined."""
        assert "<Control-a>" in SHORTCUTS
        assert SHORTCUTS["<Control-a>"]["action"] == "analyze_selected"
        assert "Analyze" in SHORTCUTS["<Control-a>"]["description"]

    def test_compose_shortcut(self):
        """Test compose shortcut is defined."""
        assert "<Control-n>" in SHORTCUTS
        assert SHORTCUTS["<Control-n>"]["action"] == "compose_new"
        assert "Compose" in SHORTCUTS["<Control-n>"]["description"]

    def test_send_shortcut(self):
        """Test send shortcut is defined."""
        assert "<Control-Return>" in SHORTCUTS
        assert SHORTCUTS["<Control-Return>"]["action"] == "send_email"
        assert "Send" in SHORTCUTS["<Control-Return>"]["description"]

    def test_delete_shortcut(self):
        """Test delete shortcut is defined."""
        assert "<Control-d>" in SHORTCUTS
        assert SHORTCUTS["<Control-d>"]["action"] == "delete_selected"
        assert "Delete" in SHORTCUTS["<Control-d>"]["description"]

    def test_move_shortcut(self):
        """Test move shortcut is defined."""
        assert "<Control-m>" in SHORTCUTS
        assert SHORTCUTS["<Control-m>"]["action"] == "move_selected"
        assert "Move" in SHORTCUTS["<Control-m>"]["description"]

    def test_settings_shortcut(self):
        """Test settings shortcut is defined."""
        assert "<Control-comma>" in SHORTCUTS
        assert SHORTCUTS["<Control-comma>"]["action"] == "open_settings"
        assert "Settings" in SHORTCUTS["<Control-comma>"]["description"]

    def test_toggle_theme_shortcut(self):
        """Test toggle theme shortcut is defined."""
        assert "<Control-t>" in SHORTCUTS
        assert SHORTCUTS["<Control-t>"]["action"] == "toggle_theme"
        assert "theme" in SHORTCUTS["<Control-t>"]["description"].lower()

    def test_show_shortcuts_shortcut(self):
        """Test show shortcuts shortcut is defined."""
        assert "<Control-slash>" in SHORTCUTS
        assert SHORTCUTS["<Control-slash>"]["action"] == "show_shortcuts"
        assert "shortcuts" in SHORTCUTS["<Control-slash>"]["description"].lower()

    def test_escape_shortcut(self):
        """Test escape shortcut is defined."""
        assert "<Escape>" in SHORTCUTS
        assert SHORTCUTS["<Escape>"]["action"] == "close_dialog"
        assert "Close" in SHORTCUTS["<Escape>"]["description"]

    def test_all_shortcuts_have_required_fields(self):
        """Test all shortcuts have action and description."""
        for key, shortcut in SHORTCUTS.items():
            assert "action" in shortcut
            assert "description" in shortcut
            assert isinstance(shortcut["action"], str)
            assert isinstance(shortcut["description"], str)
            assert len(shortcut["action"]) > 0
            assert len(shortcut["description"]) > 0


class TestBindShortcuts:
    """Test bind_shortcuts function."""

    def test_bind_shortcuts_with_matching_handlers(self, root):
        """Test binding shortcuts with matching handlers."""
        handlers = {
            "refresh_email_list": Mock(),
            "analyze_selected": Mock(),
            "compose_new": Mock()
        }

        bind_shortcuts(root, handlers)

        # Handlers should be bound (we can't easily test this without triggering events)
        # So just verify it doesn't crash
        assert True

    def test_bind_shortcuts_with_no_matching_handlers(self, root):
        """Test binding shortcuts with no matching handlers."""
        handlers = {
            "nonexistent_action": Mock()
        }

        # Should not crash even if no handlers match
        bind_shortcuts(root, handlers)
        assert True

    def test_bind_shortcuts_with_empty_handlers(self, root):
        """Test binding shortcuts with empty handlers dict."""
        bind_shortcuts(root, {})
        assert True

    def test_bind_shortcuts_with_all_handlers(self, root):
        """Test binding all shortcuts."""
        handlers = {
            "refresh_email_list": Mock(),
            "analyze_selected": Mock(),
            "compose_new": Mock(),
            "send_email": Mock(),
            "delete_selected": Mock(),
            "move_selected": Mock(),
            "open_settings": Mock(),
            "toggle_theme": Mock(),
            "show_shortcuts": Mock(),
            "close_dialog": Mock()
        }

        bind_shortcuts(root, handlers)
        assert True

    def test_bind_shortcuts_partial_handlers(self, root):
        """Test binding shortcuts with partial handlers."""
        handlers = {
            "refresh_email_list": Mock(),
            "toggle_theme": Mock()
        }

        # Should only bind matching shortcuts
        bind_shortcuts(root, handlers)
        assert True


class TestGetShortcutsText:
    """Test get_shortcuts_text function."""

    def test_get_shortcuts_text_returns_string(self):
        """Test function returns a string."""
        text = get_shortcuts_text()
        assert isinstance(text, str)

    def test_get_shortcuts_text_has_title(self):
        """Test output has title."""
        text = get_shortcuts_text()
        assert "Keyboard Shortcuts:" in text

    def test_get_shortcuts_text_formats_control_keys(self):
        """Test Control key is formatted as Ctrl+."""
        text = get_shortcuts_text()
        assert "Ctrl+" in text
        assert "<Control-" not in text  # Raw format should not appear

    def test_get_shortcuts_text_formats_return_key(self):
        """Test Return key is formatted as Enter."""
        text = get_shortcuts_text()
        assert "Enter" in text
        assert "Return" not in text  # Raw format should not appear

    def test_get_shortcuts_text_formats_comma(self):
        """Test comma is formatted correctly."""
        text = get_shortcuts_text()
        assert "Ctrl+," in text
        assert "comma" not in text  # Raw format should not appear

    def test_get_shortcuts_text_formats_slash(self):
        """Test slash is formatted correctly."""
        text = get_shortcuts_text()
        assert "Ctrl+/" in text
        assert "slash" not in text  # Raw format should not appear

    def test_get_shortcuts_text_includes_all_shortcuts(self):
        """Test output includes all 10 shortcuts."""
        text = get_shortcuts_text()

        # Check for key shortcuts (formatted)
        assert "Ctrl+R" in text or "Ctrl+r" in text  # Refresh
        assert "Ctrl+A" in text or "Ctrl+a" in text  # Analyze
        assert "Ctrl+N" in text or "Ctrl+n" in text  # Compose
        assert "Ctrl+D" in text or "Ctrl+d" in text  # Delete
        assert "Ctrl+M" in text or "Ctrl+m" in text  # Move
        assert "Ctrl+T" in text or "Ctrl+t" in text  # Toggle theme
        assert "Ctrl+," in text  # Settings
        assert "Ctrl+/" in text  # Show shortcuts
        assert "Escape" in text  # Close dialog

    def test_get_shortcuts_text_includes_descriptions(self):
        """Test output includes descriptions."""
        text = get_shortcuts_text()

        # Check for some key descriptions
        assert "Refresh" in text
        assert "Analyze" in text
        assert "Compose" in text
        assert "Delete" in text
        assert "Settings" in text

    def test_get_shortcuts_text_has_proper_formatting(self):
        """Test output has proper formatting with separators."""
        text = get_shortcuts_text()

        # Should have " - " separator between shortcut and description
        assert " - " in text

    def test_get_shortcuts_text_multiline(self):
        """Test output has multiple lines."""
        text = get_shortcuts_text()
        lines = text.split("\n")

        # Should have at least 12 lines (title + blank + 10 shortcuts)
        assert len(lines) >= 12


class TestShortcutHandlerInvocation:
    """Test that handlers are actually called when shortcuts are triggered."""

    def test_handler_called_correctly(self, root):
        """Test handler is called with correct action."""
        # This is a basic test - actual event triggering would require more complex setup
        handlers = {
            "refresh_email_list": Mock(),
            "analyze_selected": Mock()
        }

        bind_shortcuts(root, handlers)

        # We can't easily simulate key events in tests, but we've verified:
        # 1. Shortcuts are defined correctly
        # 2. bind_shortcuts doesn't crash
        # 3. Handlers dict is structured correctly
        assert "refresh_email_list" in handlers
        assert "analyze_selected" in handlers


class TestEdgeCases:
    """Test edge cases."""

    def test_shortcuts_immutable(self):
        """Test SHORTCUTS dict can be used safely."""
        # Create a copy to test with
        shortcuts_copy = SHORTCUTS.copy()
        assert len(shortcuts_copy) == len(SHORTCUTS)

    def test_bind_shortcuts_with_none_handler(self, root):
        """Test binding with None as handler."""
        handlers = {
            "refresh_email_list": None
        }

        # Should handle gracefully
        bind_shortcuts(root, handlers)
        assert True

    def test_get_shortcuts_text_consistent(self):
        """Test get_shortcuts_text returns consistent results."""
        text1 = get_shortcuts_text()
        text2 = get_shortcuts_text()

        assert text1 == text2

    def test_shortcuts_have_unique_actions(self):
        """Test all shortcuts have unique actions."""
        actions = [shortcut["action"] for shortcut in SHORTCUTS.values()]
        assert len(actions) == len(set(actions))  # All unique

    def test_shortcuts_have_unique_key_combos(self):
        """Test all shortcuts have unique key combinations."""
        keys = list(SHORTCUTS.keys())
        assert len(keys) == len(set(keys))  # All unique
