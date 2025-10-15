"""
Integration tests for SettingsManager with DatabaseManager and other components.

Tests verify:
- Real database persistence
- Settings lifecycle (load -> modify -> save -> reload)
- YAML export/import with real files
- Observer pattern with real components
- Thread-safety with concurrent operations
- Cross-component integration
"""

import pytest
import tempfile
import threading
import time
from pathlib import Path
from typing import List, Any

from mailmind.core.settings_manager import SettingsManager, SettingsValidationError, SETTINGS_SCHEMA
from mailmind.database.database_manager import DatabaseManager


class TestDatabaseIntegration:
    """Test SettingsManager integration with real DatabaseManager."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        db_manager = DatabaseManager(db_path)
        # DatabaseManager auto-initializes in __init__

        yield db_manager

        # Cleanup
        db_manager.disconnect()
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def settings_manager(self, temp_db):
        """Create SettingsManager with real database."""
        SettingsManager.reset_instance()
        manager = SettingsManager.get_instance(temp_db)
        yield manager
        SettingsManager.reset_instance()

    def test_initial_load_uses_defaults(self, settings_manager):
        """Test that initial load returns default values from schema."""
        # Reset to defaults first to ensure clean state
        settings_manager.reset_to_defaults()
        settings = settings_manager.load_settings()

        # Verify all 19 settings present
        assert len(settings) == 19

        # Verify default values match schema
        assert settings["theme"] == "dark"
        assert settings["startup_behavior"] == "normal"
        assert settings["show_notifications"] == True
        assert settings["model"] == "llama3:8b"
        assert settings["temperature"] == 0.7
        assert settings["batch_size"] == 5
        assert settings["enable_telemetry"] == False
        assert settings["log_level"] == "INFO"

    def test_save_and_reload_persistence(self, settings_manager, temp_db):
        """Test settings persist across manager instances."""
        # Modify and save settings with VALID values
        settings_manager.set_setting("theme", "light")
        settings_manager.set_setting("temperature", 0.9)
        settings_manager.set_setting("batch_size", 10)  # Valid: 1-20

        # Create new manager instance with same database
        SettingsManager.reset_instance()
        new_manager = SettingsManager.get_instance(temp_db)

        # Verify settings persisted
        assert new_manager.get_setting("theme") == "light"
        assert new_manager.get_setting("temperature") == 0.9
        assert new_manager.get_setting("batch_size") == 10

        # Verify other settings still at defaults
        assert new_manager.get_setting("startup_behavior") == "normal"

    def test_bulk_save_and_reload(self, settings_manager, temp_db):
        """Test bulk save and reload of all settings."""
        # Modify all 19 settings with VALID values
        new_settings = {
            # General (4)
            "theme": "light",
            "startup_behavior": "minimized",
            "show_notifications": False,
            "minimize_to_tray": True,
            # AI Model (4)
            "model": "mistral:7b",
            "temperature": 0.5,
            "response_length_default": "Brief",
            "response_tone_default": "Friendly",
            # Performance (4)
            "batch_size": 15,  # Valid: 1-20
            "cache_size_mb": 1024,  # Valid: 100-5000
            "use_gpu": True,
            "max_concurrent": 2,  # Valid: 1-5
            # Privacy (3)
            "enable_telemetry": True,
            "enable_crash_reports": False,
            "log_level": "DEBUG",
            # Advanced (4)
            "database_path": "custom/mailmind.db",
            "debug_mode": True,
            "auto_backup": False,
            "backup_frequency_hours": 48  # Valid: 1-168
        }

        settings_manager.save_settings(new_settings)

        # Create new manager and verify all settings
        SettingsManager.reset_instance()
        new_manager = SettingsManager.get_instance(temp_db)
        loaded_settings = new_manager.load_settings()

        for key, expected_value in new_settings.items():
            assert loaded_settings[key] == expected_value, f"Setting {key} not persisted correctly"

    def test_partial_save_preserves_other_settings(self, settings_manager):
        """Test that saving partial settings doesn't overwrite others."""
        # Set initial values
        settings_manager.set_setting("theme", "light")
        settings_manager.set_setting("startup_behavior", "tray")
        settings_manager.set_setting("batch_size", 8)

        # Save only temperature
        settings_manager.save_settings({"temperature": 0.8})

        # Verify temperature updated but others preserved
        assert settings_manager.get_setting("temperature") == 0.8
        assert settings_manager.get_setting("theme") == "light"
        assert settings_manager.get_setting("startup_behavior") == "tray"
        assert settings_manager.get_setting("batch_size") == 8

    def test_database_error_handling(self, temp_db):
        """Test graceful handling of database errors."""
        manager = SettingsManager.get_instance(temp_db)

        # Reset to defaults first
        manager.reset_to_defaults()

        # Close database to simulate error
        temp_db.disconnect()

        # load_settings should fall back to defaults on database error
        settings = manager.load_settings()
        assert len(settings) == 19
        assert settings["theme"] == "dark"  # Default value


class TestYamlIntegration:
    """Test YAML export/import with real files."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        db_manager = DatabaseManager(db_path)
        # DatabaseManager auto-initializes in __init__

        yield db_manager

        db_manager.disconnect()
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def settings_manager(self, temp_db):
        """Create SettingsManager."""
        SettingsManager.reset_instance()
        manager = SettingsManager.get_instance(temp_db)
        yield manager
        SettingsManager.reset_instance()

    @pytest.fixture
    def temp_yaml_path(self):
        """Create temporary YAML file path."""
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as f:
            yaml_path = f.name

        yield yaml_path

        Path(yaml_path).unlink(missing_ok=True)

    def test_export_import_round_trip(self, settings_manager, temp_yaml_path):
        """Test exporting to YAML and importing back preserves settings."""
        # Set custom values with VALID values
        custom_settings = {
            "theme": "light",
            "temperature": 0.85,
            "batch_size": 12,  # Valid: 1-20
            "log_level": "DEBUG",
            "show_notifications": False
        }
        settings_manager.save_settings(custom_settings)

        # Export to YAML
        settings_manager.export_to_yaml(temp_yaml_path)

        # Verify file exists
        assert Path(temp_yaml_path).exists()

        # Reset to defaults
        settings_manager.reset_to_defaults()
        assert settings_manager.get_setting("theme") == "dark"

        # Import from YAML
        settings_manager.load_from_yaml(temp_yaml_path)

        # Verify custom values restored
        for key, value in custom_settings.items():
            assert settings_manager.get_setting(key) == value

    def test_export_creates_valid_yaml_structure(self, settings_manager, temp_yaml_path):
        """Test exported YAML has correct structure."""
        import yaml

        settings_manager.export_to_yaml(temp_yaml_path)

        # Read and parse YAML
        with open(temp_yaml_path, 'r') as f:
            data = yaml.safe_load(f)

        # Verify structure - should have category sections
        assert isinstance(data, dict)

        # Should contain settings organized by category
        all_settings = {}
        for category_data in data.values():
            if isinstance(category_data, dict):
                all_settings.update(category_data)

        # Should have all 19 settings
        assert len(all_settings) >= 19

    def test_import_validates_settings(self, settings_manager, temp_yaml_path):
        """Test that importing YAML validates settings."""
        import yaml

        # Create YAML with invalid value
        invalid_data = {
            "general": {
                "theme": "invalid_theme",  # Should be "dark" or "light"
            }
        }

        with open(temp_yaml_path, 'w') as f:
            yaml.dump(invalid_data, f)

        # Import should raise validation error
        with pytest.raises(SettingsValidationError):
            settings_manager.load_from_yaml(temp_yaml_path)

    def test_export_import_with_all_categories(self, settings_manager, temp_yaml_path):
        """Test export/import preserves all setting categories."""
        # Set values in each category with VALID values
        test_settings = {
            # General
            "theme": "light",
            "startup_behavior": "tray",
            # AI Model
            "model": "mistral:7b",
            "temperature": 0.6,
            # Performance
            "batch_size": 10,  # Valid: 1-20
            "cache_size_mb": 768,  # Valid: 100-5000
            # Privacy
            "enable_telemetry": True,
            "enable_crash_reports": False,
            # Advanced
            "log_level": "DEBUG",
            "debug_mode": True
        }

        settings_manager.save_settings(test_settings)
        settings_manager.export_to_yaml(temp_yaml_path)

        # Reset and import
        settings_manager.reset_to_defaults()
        settings_manager.load_from_yaml(temp_yaml_path)

        # Verify all categories preserved
        for key, value in test_settings.items():
            assert settings_manager.get_setting(key) == value


class TestObserverIntegration:
    """Test observer pattern integration with real components."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        db_manager = DatabaseManager(db_path)
        # DatabaseManager auto-initializes in __init__

        yield db_manager

        db_manager.disconnect()
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def settings_manager(self, temp_db):
        """Create SettingsManager."""
        SettingsManager.reset_instance()
        manager = SettingsManager.get_instance(temp_db)
        yield manager
        SettingsManager.reset_instance()

    def test_observer_receives_notifications(self, settings_manager):
        """Test that observers receive setting change notifications."""
        # Ensure starting with defaults
        settings_manager.reset_to_defaults()

        notifications_received = []

        def observer(new_value):
            notifications_received.append(new_value)

        # Subscribe to theme changes
        settings_manager.subscribe("theme", observer)

        # Change theme (from default "dark" to "light")
        settings_manager.set_setting("theme", "light")

        # Verify notification received
        assert len(notifications_received) == 1
        assert notifications_received[0] == "light"

    def test_multiple_observers_all_notified(self, settings_manager):
        """Test multiple observers all receive notifications."""
        observer1_calls = []
        observer2_calls = []
        observer3_calls = []

        settings_manager.subscribe("temperature", lambda v: observer1_calls.append(v))
        settings_manager.subscribe("temperature", lambda v: observer2_calls.append(v))
        settings_manager.subscribe("temperature", lambda v: observer3_calls.append(v))

        # Change temperature
        settings_manager.set_setting("temperature", 0.9)

        # All observers should be notified
        assert observer1_calls == [0.9]
        assert observer2_calls == [0.9]
        assert observer3_calls == [0.9]

    def test_observer_unsubscribe(self, settings_manager):
        """Test unsubscribing observers stops notifications."""
        calls = []

        def observer(value):
            calls.append(value)

        settings_manager.subscribe("batch_size", observer)
        settings_manager.set_setting("batch_size", 10)  # Valid: 1-20
        assert len(calls) == 1

        # Unsubscribe
        settings_manager.unsubscribe("batch_size", observer)
        settings_manager.set_setting("batch_size", 15)  # Valid: 1-20

        # Should not receive new notification
        assert len(calls) == 1

    def test_observer_survives_save_settings(self, settings_manager):
        """Test observers receive notifications from save_settings()."""
        # Ensure starting with defaults
        settings_manager.reset_to_defaults()

        theme_changes = []
        temp_changes = []

        settings_manager.subscribe("theme", lambda v: theme_changes.append(v))
        settings_manager.subscribe("temperature", lambda v: temp_changes.append(v))

        # Save multiple settings (changing from defaults)
        settings_manager.save_settings({
            "theme": "light",  # Changed from "dark"
            "temperature": 0.8,  # Changed from 0.7
            "batch_size": 8  # Valid: 1-20
        })

        # Both subscribed settings should trigger
        assert "light" in theme_changes
        assert 0.8 in temp_changes

    def test_cross_setting_observer_pattern(self, settings_manager):
        """Test observing multiple settings simultaneously."""
        # Ensure starting with defaults
        settings_manager.reset_to_defaults()

        changes_log = []

        def log_change(setting_name):
            def observer(value):
                changes_log.append((setting_name, value))
            return observer

        # Subscribe to multiple settings
        settings_manager.subscribe("theme", log_change("theme"))
        settings_manager.subscribe("startup_behavior", log_change("startup_behavior"))
        settings_manager.subscribe("log_level", log_change("log_level"))

        # Change all three (from defaults)
        settings_manager.save_settings({
            "theme": "light",  # Changed from "dark"
            "startup_behavior": "tray",  # Changed from "normal"
            "log_level": "DEBUG"  # Changed from "INFO"
        })

        # Verify all changes logged
        assert ("theme", "light") in changes_log
        assert ("startup_behavior", "tray") in changes_log
        assert ("log_level", "DEBUG") in changes_log


class TestThreadSafetyIntegration:
    """Test thread-safety with concurrent operations on real database."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        db_manager = DatabaseManager(db_path)
        # DatabaseManager auto-initializes in __init__

        yield db_manager

        db_manager.disconnect()
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def settings_manager(self, temp_db):
        """Create SettingsManager."""
        SettingsManager.reset_instance()
        manager = SettingsManager.get_instance(temp_db)
        yield manager
        SettingsManager.reset_instance()

    def test_concurrent_reads(self, settings_manager):
        """Test multiple threads reading settings concurrently."""
        results = []
        errors = []

        def read_settings():
            try:
                settings = settings_manager.load_settings()
                results.append(len(settings))
            except Exception as e:
                errors.append(str(e))

        # Create 20 threads reading concurrently
        threads = [threading.Thread(target=read_settings) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All threads should succeed
        assert len(errors) == 0
        assert len(results) == 20
        assert all(count == 19 for count in results)

    def test_concurrent_writes(self, settings_manager):
        """Test multiple threads writing different settings concurrently."""
        errors = []

        def write_setting(setting_key, value):
            try:
                settings_manager.set_setting(setting_key, value)
            except Exception as e:
                errors.append(str(e))

        # Create threads writing different settings
        threads = [
            threading.Thread(target=write_setting, args=("theme", "light")),
            threading.Thread(target=write_setting, args=("startup_behavior", "tray")),
            threading.Thread(target=write_setting, args=("batch_size", 10)),
            threading.Thread(target=write_setting, args=("temperature", 0.8)),
            threading.Thread(target=write_setting, args=("log_level", "DEBUG")),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All writes should succeed
        assert len(errors) == 0

        # Verify all settings written
        assert settings_manager.get_setting("theme") == "light"
        assert settings_manager.get_setting("startup_behavior") == "tray"
        assert settings_manager.get_setting("batch_size") == 10
        assert settings_manager.get_setting("temperature") == 0.8
        assert settings_manager.get_setting("log_level") == "DEBUG"

    def test_concurrent_observers_notification(self, settings_manager):
        """Test observer notifications work correctly under concurrent modifications."""
        notifications = []
        lock = threading.Lock()

        def observer(value):
            with lock:
                notifications.append(value)

        settings_manager.subscribe("batch_size", observer)

        # Multiple threads changing batch_size
        def change_batch_size(value):
            settings_manager.set_setting("batch_size", value)

        threads = [
            threading.Thread(target=change_batch_size, args=(5,)),
            threading.Thread(target=change_batch_size, args=(7,)),
            threading.Thread(target=change_batch_size, args=(10,)),
            threading.Thread(target=change_batch_size, args=(12,)),
            threading.Thread(target=change_batch_size, args=(15,)),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should receive notifications for all changes
        # (exact count may vary due to race conditions, but should have some notifications)
        assert len(notifications) >= 1
        assert all(isinstance(n, int) for n in notifications)


class TestSettingsLifecycle:
    """Test complete settings lifecycle scenarios."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        db_manager = DatabaseManager(db_path)
        # DatabaseManager auto-initializes in __init__

        yield db_manager

        db_manager.disconnect()
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def settings_manager(self, temp_db):
        """Create SettingsManager."""
        SettingsManager.reset_instance()
        manager = SettingsManager.get_instance(temp_db)
        yield manager
        SettingsManager.reset_instance()

    def test_typical_user_workflow(self, settings_manager, temp_db):
        """Test a typical user workflow: load -> modify -> save -> reload."""
        # 0. Reset to ensure clean state
        settings_manager.reset_to_defaults()

        # 1. Initial load (defaults)
        initial_settings = settings_manager.load_settings()
        assert initial_settings["theme"] == "dark"
        assert initial_settings["temperature"] == 0.7

        # 2. User modifies settings
        settings_manager.set_setting("theme", "light")
        settings_manager.set_setting("temperature", 0.9)
        settings_manager.set_setting("startup_behavior", "minimized")

        # 3. Application restarts - create new manager instance
        SettingsManager.reset_instance()
        new_manager = SettingsManager.get_instance(temp_db)

        # 4. Load settings - should have persisted changes
        reloaded_settings = new_manager.load_settings()
        assert reloaded_settings["theme"] == "light"
        assert reloaded_settings["temperature"] == 0.9
        assert reloaded_settings["startup_behavior"] == "minimized"

        # 5. User resets to defaults
        new_manager.reset_to_defaults()

        # 6. Settings should be back to defaults
        assert new_manager.get_setting("theme") == "dark"
        assert new_manager.get_setting("temperature") == 0.7
        assert new_manager.get_setting("startup_behavior") == "normal"

    def test_export_backup_restore_workflow(self, settings_manager, temp_db):
        """Test workflow: customize -> export backup -> break settings -> restore."""
        # 1. Customize settings
        custom_settings = {
            "theme": "light",
            "startup_behavior": "tray",
            "temperature": 0.85,
            "batch_size": 12,
            "log_level": "DEBUG"
        }
        settings_manager.save_settings(custom_settings)

        # 2. Export backup
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as f:
            backup_path = f.name

        try:
            settings_manager.export_to_yaml(backup_path)

            # 3. "Break" settings by resetting
            settings_manager.reset_to_defaults()
            assert settings_manager.get_setting("theme") == "dark"

            # 4. Restore from backup
            settings_manager.load_from_yaml(backup_path)

            # 5. Verify settings restored
            for key, value in custom_settings.items():
                assert settings_manager.get_setting(key) == value
        finally:
            Path(backup_path).unlink(missing_ok=True)

    def test_validation_prevents_corruption(self, settings_manager):
        """Test that validation prevents saving corrupted settings."""
        # Reset to ensure clean state
        settings_manager.reset_to_defaults()

        # Try to save invalid settings
        invalid_settings = {
            "theme": "invalid_theme",
            "temperature": 5.0,  # Out of range
            "batch_size": -10    # Invalid
        }

        # Should raise validation error
        with pytest.raises(SettingsValidationError):
            settings_manager.save_settings(invalid_settings)

        # Settings should remain at defaults
        assert settings_manager.get_setting("theme") == "dark"
        assert settings_manager.get_setting("temperature") == 0.7
        assert settings_manager.get_setting("batch_size") == 5
