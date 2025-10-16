"""
Unit tests for Security Settings UI.

Tests Story 3.2 AC5, AC8:
- Security level dropdown in Settings dialog
- Override option checkbox
- Settings persistence (security_level, allow_security_override)
"""

import unittest
from unittest.mock import Mock
import customtkinter as ctk


class TestSecuritySettings(unittest.TestCase):
    """Test security settings UI in SettingsDialog."""

    def setUp(self):
        """Set up test fixtures."""
        # Create root window for testing
        self.root = ctk.CTk()
        self.root.withdraw()  # Hide window during tests

    def tearDown(self):
        """Clean up after tests."""
        try:
            self.root.destroy()
        except:
            pass

    def test_settings_dialog_has_security_settings(self):
        """Test SettingsDialog includes security_level and allow_security_override."""
        from mailmind.ui.dialogs.settings_dialog import SettingsDialog

        # Use default settings to ensure all required keys are present
        dialog = SettingsDialog(self.root)
        dialog.withdraw()

        # Check security_level_var exists
        self.assertTrue(hasattr(dialog, "security_level_var"))
        self.assertEqual(dialog.security_level_var.get(), "Normal")

        # Check allow_override_var exists
        self.assertTrue(hasattr(dialog, "allow_override_var"))
        self.assertEqual(dialog.allow_override_var.get(), False)

        dialog.destroy()

    def test_security_level_default_is_normal(self):
        """Test security_level defaults to Normal."""
        from mailmind.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(self.root)
        dialog.withdraw()

        # Check default settings
        default_settings = dialog._get_default_settings()
        self.assertEqual(default_settings["security_level"], "Normal")
        self.assertEqual(default_settings["allow_security_override"], False)

        dialog.destroy()

    def test_security_level_options(self):
        """Test security_level can be set to Strict, Normal, or Permissive."""
        from mailmind.ui.dialogs.settings_dialog import SettingsDialog

        # Test Strict
        dialog = SettingsDialog(self.root)
        dialog.withdraw()
        default_settings = dialog._get_default_settings()
        default_settings["security_level"] = "Strict"

        dialog2 = SettingsDialog(self.root, current_settings=default_settings)
        dialog2.withdraw()
        self.assertEqual(dialog2.security_level_var.get(), "Strict")
        dialog.destroy()
        dialog2.destroy()

        # Test Normal
        default_settings["security_level"] = "Normal"
        dialog = SettingsDialog(self.root, current_settings=default_settings)
        dialog.withdraw()
        self.assertEqual(dialog.security_level_var.get(), "Normal")
        dialog.destroy()

        # Test Permissive
        default_settings["security_level"] = "Permissive"
        dialog = SettingsDialog(self.root, current_settings=default_settings)
        dialog.withdraw()
        self.assertEqual(dialog.security_level_var.get(), "Permissive")
        dialog.destroy()

    def test_allow_security_override_options(self):
        """Test allow_security_override can be True or False."""
        from mailmind.ui.dialogs.settings_dialog import SettingsDialog

        # Test enabled
        dialog = SettingsDialog(self.root)
        dialog.withdraw()
        default_settings = dialog._get_default_settings()
        default_settings["allow_security_override"] = True

        dialog2 = SettingsDialog(self.root, current_settings=default_settings)
        dialog2.withdraw()
        self.assertEqual(dialog2.allow_override_var.get(), True)
        dialog.destroy()
        dialog2.destroy()

        # Test disabled
        default_settings["allow_security_override"] = False
        dialog = SettingsDialog(self.root, current_settings=default_settings)
        dialog.withdraw()
        self.assertEqual(dialog.allow_override_var.get(), False)
        dialog.destroy()

    def test_security_settings_saved_correctly(self):
        """Test security settings are saved when _get_current_settings is called."""
        from mailmind.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(self.root)
        dialog.withdraw()

        # Change security settings
        dialog.security_level_var.set("Strict")
        dialog.allow_override_var.set(True)

        # Get current settings
        current_settings = dialog._get_current_settings()

        # Check security settings were saved
        self.assertEqual(current_settings["security_level"], "Strict")
        self.assertEqual(current_settings["allow_security_override"], True)

        dialog.destroy()

    def test_security_desc_label_exists(self):
        """Test security description label exists and shows correct text."""
        from mailmind.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(self.root)
        dialog.withdraw()

        # Check security_desc_label exists
        self.assertTrue(hasattr(dialog, "security_desc_label"))

        # Check label text contains "Normal" description (default is Normal)
        label_text = dialog.security_desc_label.cget("text")
        self.assertIn("high/medium", label_text.lower())

        dialog.destroy()


if __name__ == "__main__":
    unittest.main()
