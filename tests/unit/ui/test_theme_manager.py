"""
Unit tests for ThemeManager

Tests Story 2.3 AC1: CustomTkinter Framework with Dark/Light Theme
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from mailmind.ui.theme_manager import ThemeManager


class TestThemeManagerInitialization:
    """Test ThemeManager initialization and setup."""

    def test_init_without_database(self):
        """Should initialize with default theme when no database provided."""
        theme_mgr = ThemeManager(db_manager=None)

        assert theme_mgr.get_current_theme() in ["dark", "light"]
        assert theme_mgr.db_manager is None

    def test_init_with_database_no_saved_preference(self):
        """Should detect system theme when database has no saved preference."""
        mock_db = Mock()
        mock_db.get_preference.return_value = None

        theme_mgr = ThemeManager(db_manager=mock_db)

        mock_db.get_preference.assert_called_once_with("ui_theme")
        assert theme_mgr.get_current_theme() in ["dark", "light"]

    def test_init_with_database_saved_dark_theme(self):
        """Should load dark theme from database."""
        mock_db = Mock()
        mock_db.get_preference.return_value = "dark"

        theme_mgr = ThemeManager(db_manager=mock_db)

        assert theme_mgr.get_current_theme() == "dark"

    def test_init_with_database_saved_light_theme(self):
        """Should load light theme from database."""
        mock_db = Mock()
        mock_db.get_preference.return_value = "light"

        theme_mgr = ThemeManager(db_manager=mock_db)

        assert theme_mgr.get_current_theme() == "light"

    def test_init_with_database_invalid_preference(self):
        """Should fall back to system theme when database has invalid preference."""
        mock_db = Mock()
        mock_db.get_preference.return_value = "invalid_theme"

        theme_mgr = ThemeManager(db_manager=mock_db)

        assert theme_mgr.get_current_theme() in ["dark", "light"]

    def test_init_with_database_error(self):
        """Should fall back to system theme when database raises error."""
        mock_db = Mock()
        mock_db.get_preference.side_effect = Exception("Database error")

        theme_mgr = ThemeManager(db_manager=mock_db)

        assert theme_mgr.get_current_theme() in ["dark", "light"]


class TestSystemThemeDetection:
    """Test system theme preference detection."""

    @patch('darkdetect.isDark')
    def test_detect_dark_theme(self, mock_is_dark):
        """Should detect dark theme from system."""
        mock_is_dark.return_value = True

        theme_mgr = ThemeManager(db_manager=None)

        assert theme_mgr.get_current_theme() == "dark"

    @patch('darkdetect.isDark')
    def test_detect_light_theme(self, mock_is_dark):
        """Should detect light theme from system."""
        mock_is_dark.return_value = False

        theme_mgr = ThemeManager(db_manager=None)

        assert theme_mgr.get_current_theme() == "light"

    @patch('darkdetect.isDark')
    def test_detect_unknown_theme(self, mock_is_dark):
        """Should default to dark when system theme cannot be detected."""
        mock_is_dark.return_value = None

        theme_mgr = ThemeManager(db_manager=None)

        assert theme_mgr.get_current_theme() == "dark"

    @patch('darkdetect.isDark')
    def test_detect_theme_error(self, mock_is_dark):
        """Should default to dark when detection raises error."""
        mock_is_dark.side_effect = Exception("Detection error")

        theme_mgr = ThemeManager(db_manager=None)

        assert theme_mgr.get_current_theme() == "dark"


class TestThemeSwitching:
    """Test theme switching functionality."""

    @patch('mailmind.ui.theme_manager.ctk.set_appearance_mode')
    def test_set_theme_dark_to_light(self, mock_set_appearance):
        """Should switch from dark to light theme."""
        mock_db = Mock()
        mock_db.get_preference.return_value = "dark"

        theme_mgr = ThemeManager(db_manager=mock_db)
        theme_mgr.set_theme("light")

        assert theme_mgr.get_current_theme() == "light"
        mock_set_appearance.assert_called_with("light")
        mock_db.set_preference.assert_called_with("ui_theme", "light")

    @patch('mailmind.ui.theme_manager.ctk.set_appearance_mode')
    def test_set_theme_light_to_dark(self, mock_set_appearance):
        """Should switch from light to dark theme."""
        mock_db = Mock()
        mock_db.get_preference.return_value = "light"

        theme_mgr = ThemeManager(db_manager=mock_db)
        theme_mgr.set_theme("dark")

        assert theme_mgr.get_current_theme() == "dark"
        mock_set_appearance.assert_called_with("dark")
        mock_db.set_preference.assert_called_with("ui_theme", "dark")

    @patch('mailmind.ui.theme_manager.ctk.set_appearance_mode')
    def test_set_theme_same_theme(self, mock_set_appearance):
        """Should not trigger changes when setting same theme."""
        mock_db = Mock()
        mock_db.get_preference.return_value = "dark"

        theme_mgr = ThemeManager(db_manager=mock_db)
        theme_mgr.set_theme("dark")

        # Should not call set_appearance_mode or set_preference again
        mock_set_appearance.assert_not_called()

    @patch('mailmind.ui.theme_manager.ctk.set_appearance_mode')
    def test_set_theme_invalid_mode(self, mock_set_appearance):
        """Should raise ValueError for invalid theme mode."""
        theme_mgr = ThemeManager(db_manager=None)

        with pytest.raises(ValueError, match="Invalid theme mode"):
            theme_mgr.set_theme("invalid")

    @patch('mailmind.ui.theme_manager.ctk.set_appearance_mode')
    def test_toggle_theme_dark_to_light(self, mock_set_appearance):
        """Should toggle from dark to light."""
        mock_db = Mock()
        mock_db.get_preference.return_value = "dark"

        theme_mgr = ThemeManager(db_manager=mock_db)
        theme_mgr.toggle_theme()

        assert theme_mgr.get_current_theme() == "light"

    @patch('mailmind.ui.theme_manager.ctk.set_appearance_mode')
    def test_toggle_theme_light_to_dark(self, mock_set_appearance):
        """Should toggle from light to dark."""
        mock_db = Mock()
        mock_db.get_preference.return_value = "light"

        theme_mgr = ThemeManager(db_manager=mock_db)
        theme_mgr.toggle_theme()

        assert theme_mgr.get_current_theme() == "dark"


class TestThemePersistence:
    """Test theme persistence to database."""

    @patch('mailmind.ui.theme_manager.ctk.set_appearance_mode')
    def test_save_theme_success(self, mock_set_appearance):
        """Should save theme to database successfully."""
        mock_db = Mock()
        mock_db.get_preference.return_value = "dark"

        theme_mgr = ThemeManager(db_manager=mock_db)
        theme_mgr.set_theme("light")

        mock_db.set_preference.assert_called_once_with("ui_theme", "light")

    @patch('mailmind.ui.theme_manager.ctk.set_appearance_mode')
    def test_save_theme_database_error(self, mock_set_appearance):
        """Should handle database save error gracefully."""
        mock_db = Mock()
        mock_db.get_preference.return_value = "dark"
        mock_db.set_preference.side_effect = Exception("Database error")

        theme_mgr = ThemeManager(db_manager=mock_db)
        theme_mgr.set_theme("light")  # Should not raise exception

        assert theme_mgr.get_current_theme() == "light"

    @patch('mailmind.ui.theme_manager.ctk.set_appearance_mode')
    def test_no_save_without_database(self, mock_set_appearance):
        """Should not attempt to save when no database provided."""
        theme_mgr = ThemeManager(db_manager=None)
        theme_mgr.set_theme("light")  # Should not raise exception

        assert theme_mgr.get_current_theme() == "light"


class TestThemeObservers:
    """Test theme change observer pattern."""

    @patch('mailmind.ui.theme_manager.ctk.set_appearance_mode')
    def test_add_observer(self, mock_set_appearance):
        """Should add observer and notify on theme change."""
        theme_mgr = ThemeManager(db_manager=None)

        callback = Mock()
        theme_mgr.add_observer(callback)
        theme_mgr.set_theme("light" if theme_mgr.get_current_theme() == "dark" else "dark")

        callback.assert_called_once()

    @patch('mailmind.ui.theme_manager.ctk.set_appearance_mode')
    def test_remove_observer(self, mock_set_appearance):
        """Should remove observer and not notify."""
        theme_mgr = ThemeManager(db_manager=None)

        callback = Mock()
        theme_mgr.add_observer(callback)
        theme_mgr.remove_observer(callback)
        theme_mgr.set_theme("light" if theme_mgr.get_current_theme() == "dark" else "dark")

        callback.assert_not_called()

    @patch('mailmind.ui.theme_manager.ctk.set_appearance_mode')
    def test_multiple_observers(self, mock_set_appearance):
        """Should notify all observers on theme change."""
        theme_mgr = ThemeManager(db_manager=None)

        callback1 = Mock()
        callback2 = Mock()
        theme_mgr.add_observer(callback1)
        theme_mgr.add_observer(callback2)

        theme_mgr.set_theme("light" if theme_mgr.get_current_theme() == "dark" else "dark")

        callback1.assert_called_once()
        callback2.assert_called_once()

    @patch('mailmind.ui.theme_manager.ctk.set_appearance_mode')
    def test_observer_error_handling(self, mock_set_appearance):
        """Should handle observer errors gracefully."""
        theme_mgr = ThemeManager(db_manager=None)

        callback_error = Mock(side_effect=Exception("Observer error"))
        callback_ok = Mock()
        theme_mgr.add_observer(callback_error)
        theme_mgr.add_observer(callback_ok)

        theme_mgr.set_theme("light" if theme_mgr.get_current_theme() == "dark" else "dark")

        # Both callbacks should be called despite error in first one
        callback_error.assert_called_once()
        callback_ok.assert_called_once()


class TestColorManagement:
    """Test color retrieval and management."""

    def test_get_color_dark_theme(self):
        """Should return correct colors for dark theme."""
        mock_db = Mock()
        mock_db.get_preference.return_value = "dark"

        theme_mgr = ThemeManager(db_manager=mock_db)

        assert theme_mgr.get_color("dark", "bg") == "#1a1a1a"
        assert theme_mgr.get_color("dark", "fg") == "#e0e0e0"
        assert theme_mgr.get_color("dark", "accent") == "#4a9eff"

    def test_get_color_light_theme(self):
        """Should return correct colors for light theme."""
        mock_db = Mock()
        mock_db.get_preference.return_value = "light"

        theme_mgr = ThemeManager(db_manager=mock_db)

        assert theme_mgr.get_color("light", "bg") == "#ffffff"
        assert theme_mgr.get_color("light", "fg") == "#1a1a1a"
        assert theme_mgr.get_color("light", "accent") == "#2563eb"

    def test_get_priority_colors(self):
        """Should return correct priority colors."""
        theme_mgr = ThemeManager(db_manager=None)

        assert theme_mgr.get_color("priority", "high") == "#ef4444"
        assert theme_mgr.get_color("priority", "medium") == "#f59e0b"
        assert theme_mgr.get_color("priority", "low") == "#3b82f6"

    def test_get_priority_color_high(self):
        """Should return high priority color."""
        theme_mgr = ThemeManager(db_manager=None)

        assert theme_mgr.get_priority_color("high") == "#ef4444"
        assert theme_mgr.get_priority_color("High") == "#ef4444"

    def test_get_priority_color_medium(self):
        """Should return medium priority color."""
        theme_mgr = ThemeManager(db_manager=None)

        assert theme_mgr.get_priority_color("medium") == "#f59e0b"
        assert theme_mgr.get_priority_color("Medium") == "#f59e0b"

    def test_get_priority_color_low(self):
        """Should return low priority color."""
        theme_mgr = ThemeManager(db_manager=None)

        assert theme_mgr.get_priority_color("low") == "#3b82f6"
        assert theme_mgr.get_priority_color("Low") == "#3b82f6"

    def test_get_priority_color_invalid(self):
        """Should return medium color for invalid priority."""
        theme_mgr = ThemeManager(db_manager=None)

        assert theme_mgr.get_priority_color("invalid") == "#f59e0b"

    def test_get_theme_colors(self):
        """Should return all colors for current theme."""
        mock_db = Mock()
        mock_db.get_preference.return_value = "dark"

        theme_mgr = ThemeManager(db_manager=mock_db)
        colors = theme_mgr.get_theme_colors()

        assert colors["bg"] == "#1a1a1a"
        assert colors["fg"] == "#e0e0e0"
        assert colors["accent"] == "#4a9eff"
        assert colors["hover"] == "#2a2a2a"
        assert colors["selected"] == "#3a3a3a"

    def test_apply_to_widget(self):
        """Should apply theme colors to widget."""
        theme_mgr = ThemeManager(db_manager=None)

        mock_widget = Mock()
        theme_mgr.apply_to_widget(mock_widget, fg_color="bg", text_color="fg")

        # Verify configure was called with correct colors
        assert mock_widget.configure.called
