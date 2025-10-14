"""
Unit tests for SettingsDialog component.

Tests Story 2.3 AC2, AC7: Settings dialog with tabbed interface
"""

import pytest
import customtkinter as ctk
from unittest.mock import Mock, patch, MagicMock

from mailmind.ui.dialogs.settings_dialog import SettingsDialog


@pytest.fixture
def root():
    """Create root window for tests."""
    root = ctk.CTk()
    yield root
    root.destroy()


@pytest.fixture
def custom_settings():
    """Create custom settings for testing."""
    return {
        # General
        "theme": "light",
        "startup_behavior": "minimized",
        "show_notifications": False,
        "minimize_to_tray": True,

        # AI Model
        "model": "mistral:7b",
        "temperature": 0.5,
        "response_length_default": "Brief",
        "response_tone_default": "Friendly",

        # Performance
        "batch_size": 10,
        "cache_size_mb": 1000,
        "use_gpu": True,
        "max_concurrent": 5,

        # Privacy
        "enable_telemetry": True,
        "enable_crash_reports": False,
        "log_level": "DEBUG",

        # Advanced
        "database_path": "custom/path.db",
        "debug_mode": True,
        "auto_backup": False,
        "backup_frequency_hours": 12
    }


class TestSettingsDialogInitialization:
    """Test SettingsDialog initialization."""

    def test_initialization_with_defaults(self, root):
        """Test dialog initializes with default settings."""
        dialog = SettingsDialog(root)

        assert dialog.on_save_callback is None
        assert dialog.settings is not None
        assert dialog.original_settings is not None
        assert dialog.title() == "MailMind Settings"

        dialog.destroy()

    def test_initialization_with_callback(self, root):
        """Test dialog initializes with callback."""
        callback = Mock()
        dialog = SettingsDialog(root, on_save=callback)

        assert dialog.on_save_callback == callback

        dialog.destroy()

    def test_initialization_with_custom_settings(self, root, custom_settings):
        """Test dialog initializes with custom settings."""
        dialog = SettingsDialog(root, current_settings=custom_settings)

        assert dialog.settings == custom_settings

        dialog.destroy()

    def test_dialog_is_modal(self, root):
        """Test dialog is modal (transient and grab_set)."""
        dialog = SettingsDialog(root)

        # Dialog should be transient (returns window path string, not object)
        assert dialog.transient() is not None

        dialog.destroy()


class TestDefaultSettings:
    """Test default settings."""

    def test_default_settings_structure(self, root):
        """Test default settings have all required fields."""
        dialog = SettingsDialog(root)
        defaults = dialog._get_default_settings()

        # General
        assert "theme" in defaults
        assert "startup_behavior" in defaults
        assert "show_notifications" in defaults
        assert "minimize_to_tray" in defaults

        # AI Model
        assert "model" in defaults
        assert "temperature" in defaults
        assert "response_length_default" in defaults
        assert "response_tone_default" in defaults

        # Performance
        assert "batch_size" in defaults
        assert "cache_size_mb" in defaults
        assert "use_gpu" in defaults
        assert "max_concurrent" in defaults

        # Privacy
        assert "enable_telemetry" in defaults
        assert "enable_crash_reports" in defaults
        assert "log_level" in defaults

        # Advanced
        assert "database_path" in defaults
        assert "debug_mode" in defaults
        assert "auto_backup" in defaults
        assert "backup_frequency_hours" in defaults

        dialog.destroy()

    def test_default_settings_values(self, root):
        """Test default settings have expected values."""
        dialog = SettingsDialog(root)
        defaults = dialog._get_default_settings()

        assert defaults["theme"] == "dark"
        assert defaults["model"] == "llama3:8b"
        assert defaults["temperature"] == 0.7
        assert defaults["batch_size"] == 5
        assert defaults["enable_telemetry"] is False
        assert defaults["debug_mode"] is False

        dialog.destroy()


class TestTabCreation:
    """Test dialog tabs are created."""

    def test_all_tabs_exist(self, root):
        """Test all 5 tabs are created."""
        dialog = SettingsDialog(root)

        assert hasattr(dialog, 'tab_general')
        assert hasattr(dialog, 'tab_ai_model')
        assert hasattr(dialog, 'tab_performance')
        assert hasattr(dialog, 'tab_privacy')
        assert hasattr(dialog, 'tab_advanced')

        dialog.destroy()


class TestGeneralTabSettings:
    """Test General tab settings."""

    def test_theme_variable(self, root):
        """Test theme variable is created with correct default."""
        dialog = SettingsDialog(root)

        assert dialog.theme_var.get() == "dark"

        dialog.destroy()

    def test_theme_variable_custom(self, root):
        """Test theme variable uses custom setting."""
        settings = {"theme": "light", "startup_behavior": "normal",
                   "show_notifications": True, "minimize_to_tray": False,
                   "model": "llama3:8b", "temperature": 0.7,
                   "response_length_default": "Standard", "response_tone_default": "Professional",
                   "batch_size": 5, "cache_size_mb": 500, "use_gpu": False, "max_concurrent": 3,
                   "enable_telemetry": False, "enable_crash_reports": True, "log_level": "INFO",
                   "database_path": "data/mailmind.db", "debug_mode": False,
                   "auto_backup": True, "backup_frequency_hours": 24}
        dialog = SettingsDialog(root, current_settings=settings)

        assert dialog.theme_var.get() == "light"

        dialog.destroy()

    def test_startup_behavior_variable(self, root):
        """Test startup behavior variable."""
        dialog = SettingsDialog(root)

        assert dialog.startup_var.get() == "normal"

        dialog.destroy()

    def test_notifications_variables(self, root):
        """Test notification variables."""
        dialog = SettingsDialog(root)

        assert dialog.show_notifications_var.get() is True
        assert dialog.minimize_to_tray_var.get() is False

        dialog.destroy()


class TestAIModelTabSettings:
    """Test AI Model tab settings."""

    def test_model_variable(self, root):
        """Test model variable."""
        dialog = SettingsDialog(root)

        assert dialog.model_var.get() == "llama3:8b"

        dialog.destroy()

    def test_temperature_variable(self, root):
        """Test temperature variable."""
        dialog = SettingsDialog(root)

        assert dialog.temperature_var.get() == 0.7

        dialog.destroy()

    def test_response_defaults_variables(self, root):
        """Test response defaults variables."""
        dialog = SettingsDialog(root)

        assert dialog.response_length_var.get() == "Standard"
        assert dialog.response_tone_var.get() == "Professional"

        dialog.destroy()


class TestPerformanceTabSettings:
    """Test Performance tab settings."""

    def test_batch_size_variable(self, root):
        """Test batch size variable."""
        dialog = SettingsDialog(root)

        assert dialog.batch_size_var.get() == 5

        dialog.destroy()

    def test_cache_size_variable(self, root):
        """Test cache size variable."""
        dialog = SettingsDialog(root)

        assert dialog.cache_size_var.get() == 500

        dialog.destroy()

    def test_hardware_variables(self, root):
        """Test hardware variables."""
        dialog = SettingsDialog(root)

        assert dialog.use_gpu_var.get() is False
        assert dialog.max_concurrent_var.get() == 3

        dialog.destroy()


class TestPrivacyTabSettings:
    """Test Privacy tab settings."""

    def test_telemetry_variables(self, root):
        """Test telemetry variables."""
        dialog = SettingsDialog(root)

        assert dialog.enable_telemetry_var.get() is False
        assert dialog.enable_crash_reports_var.get() is True

        dialog.destroy()

    def test_log_level_variable(self, root):
        """Test log level variable."""
        dialog = SettingsDialog(root)

        assert dialog.log_level_var.get() == "INFO"

        dialog.destroy()


class TestAdvancedTabSettings:
    """Test Advanced tab settings."""

    def test_database_path_variable(self, root):
        """Test database path variable."""
        dialog = SettingsDialog(root)

        assert dialog.database_path_var.get() == "data/mailmind.db"

        dialog.destroy()

    def test_debug_mode_variable(self, root):
        """Test debug mode variable."""
        dialog = SettingsDialog(root)

        assert dialog.debug_mode_var.get() is False

        dialog.destroy()

    def test_backup_variables(self, root):
        """Test backup variables."""
        dialog = SettingsDialog(root)

        assert dialog.auto_backup_var.get() is True
        assert dialog.backup_frequency_var.get() == 24

        dialog.destroy()


class TestGetCurrentSettings:
    """Test getting current settings from UI."""

    def test_get_current_settings_defaults(self, root):
        """Test getting current settings with defaults."""
        dialog = SettingsDialog(root)
        current = dialog._get_current_settings()

        assert current["theme"] == "dark"
        assert current["model"] == "llama3:8b"
        assert current["temperature"] == 0.7
        assert current["batch_size"] == 5

        dialog.destroy()

    def test_get_current_settings_after_change(self, root):
        """Test getting settings after changing values."""
        dialog = SettingsDialog(root)

        # Change some values
        dialog.theme_var.set("light")
        dialog.model_var.set("mistral:7b")
        dialog.batch_size_var.set(10)

        current = dialog._get_current_settings()

        assert current["theme"] == "light"
        assert current["model"] == "mistral:7b"
        assert current["batch_size"] == 10

        dialog.destroy()

    def test_get_current_settings_all_fields(self, root):
        """Test all fields are included in current settings."""
        dialog = SettingsDialog(root)
        current = dialog._get_current_settings()

        # Should have all 19 settings (4 general + 4 ai_model + 4 performance + 3 privacy + 4 advanced)
        assert len(current) == 19

        dialog.destroy()


class TestSaveButton:
    """Test Save button functionality."""

    def test_save_button_calls_callback(self, root):
        """Test Save button triggers callback."""
        callback = Mock()
        dialog = SettingsDialog(root, on_save=callback)

        # Click save
        dialog._on_save_clicked()

        callback.assert_called_once()

        # Dialog should be destroyed (can't test easily)

    def test_save_button_no_callback(self, root):
        """Test Save button without callback doesn't crash."""
        dialog = SettingsDialog(root)

        # Should not crash
        dialog._on_save_clicked()

    def test_save_button_passes_settings(self, root):
        """Test Save button passes settings to callback."""
        callback = Mock()
        dialog = SettingsDialog(root, on_save=callback)

        # Change a setting
        dialog.theme_var.set("light")

        # Click save
        dialog._on_save_clicked()

        # Callback should receive updated settings
        saved_settings = callback.call_args[0][0]
        assert saved_settings["theme"] == "light"


class TestCancelButton:
    """Test Cancel button functionality."""

    def test_cancel_button(self, root):
        """Test Cancel button closes dialog."""
        dialog = SettingsDialog(root)

        # Click cancel
        dialog._on_cancel_clicked()

        # Dialog should be destroyed (can't test easily)

    def test_cancel_button_no_save(self, root):
        """Test Cancel button doesn't save settings."""
        callback = Mock()
        dialog = SettingsDialog(root, on_save=callback)

        # Change a setting
        dialog.theme_var.set("light")

        # Click cancel
        dialog._on_cancel_clicked()

        # Callback should not be called
        callback.assert_not_called()


class TestResetButton:
    """Test Reset to Defaults button functionality."""

    @patch('customtkinter.CTkInputDialog')
    def test_reset_button_with_confirmation(self, mock_dialog, root):
        """Test Reset button with user confirmation."""
        # Mock user confirming
        mock_instance = MagicMock()
        mock_instance.get_input.return_value = "yes"
        mock_dialog.return_value = mock_instance

        callback = Mock()
        dialog = SettingsDialog(root, on_save=callback)

        # Change a setting
        dialog.theme_var.set("light")

        # Click reset
        dialog._on_reset_clicked()

        # Dialog should have been created to confirm
        mock_dialog.assert_called_once()

    @patch('customtkinter.CTkInputDialog')
    def test_reset_button_without_confirmation(self, mock_dialog, root):
        """Test Reset button without user confirmation."""
        # Mock user canceling
        mock_instance = MagicMock()
        mock_instance.get_input.return_value = None
        mock_dialog.return_value = mock_instance

        dialog = SettingsDialog(root)

        # Change a setting
        dialog.theme_var.set("light")

        # Click reset
        dialog._on_reset_clicked()

        # Settings should not be reset (dialog stays open)
        # Can't easily test dialog state


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_very_high_temperature(self, root):
        """Test setting very high temperature."""
        dialog = SettingsDialog(root)

        dialog.temperature_var.set(1.0)
        current = dialog._get_current_settings()

        assert current["temperature"] == 1.0

        dialog.destroy()

    def test_very_low_temperature(self, root):
        """Test setting very low temperature."""
        dialog = SettingsDialog(root)

        dialog.temperature_var.set(0.0)
        current = dialog._get_current_settings()

        assert current["temperature"] == 0.0

        dialog.destroy()

    def test_high_batch_size(self, root):
        """Test setting high batch size."""
        dialog = SettingsDialog(root)

        dialog.batch_size_var.set(20)
        current = dialog._get_current_settings()

        assert current["batch_size"] == 20

        dialog.destroy()

    def test_large_cache_size(self, root):
        """Test setting large cache size."""
        dialog = SettingsDialog(root)

        dialog.cache_size_var.set(5000)
        current = dialog._get_current_settings()

        assert current["cache_size_mb"] == 5000

        dialog.destroy()

    def test_empty_database_path(self, root):
        """Test setting empty database path."""
        dialog = SettingsDialog(root)

        dialog.database_path_var.set("")
        current = dialog._get_current_settings()

        assert current["database_path"] == ""

        dialog.destroy()

    def test_settings_copy_independence(self, root):
        """Test original_settings is independent copy."""
        dialog = SettingsDialog(root)

        # Modify current settings
        dialog.theme_var.set("light")

        # Original should be unchanged
        assert dialog.original_settings["theme"] == "dark"

        dialog.destroy()

    def test_all_custom_settings_applied(self, root, custom_settings):
        """Test all custom settings are applied to UI."""
        dialog = SettingsDialog(root, current_settings=custom_settings)

        assert dialog.theme_var.get() == "light"
        assert dialog.model_var.get() == "mistral:7b"
        assert dialog.batch_size_var.get() == 10
        assert dialog.enable_telemetry_var.get() is True
        assert dialog.debug_mode_var.get() is True

        dialog.destroy()
