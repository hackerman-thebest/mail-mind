"""
Unit tests for SettingsManager.

Tests Story 2.4 AC1, AC3, AC6, AC7, AC8:
- AC1: Settings storage in user_preferences table
- AC3: SettingsManager class with methods
- AC6: Settings validation
- AC7: Default settings
- AC8: Observer pattern for change notifications
"""

import pytest
import tempfile
import os
import threading
import time
from unittest.mock import Mock, MagicMock, patch

from mailmind.core.settings_manager import (
    SettingsManager,
    SETTINGS_SCHEMA,
    SettingsValidationError
)


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        db_path = tmp.name
    yield db_path
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def mock_db_manager():
    """Create mock DatabaseManager."""
    mock_db = Mock()
    mock_db.get_preference = Mock(return_value=None)
    mock_db.set_preference = Mock(return_value=True)
    mock_db.get_all_preferences = Mock(return_value={})
    return mock_db


@pytest.fixture
def settings_manager(mock_db_manager):
    """Create SettingsManager instance with mock database."""
    # Reset singleton
    SettingsManager.reset_instance()

    manager = SettingsManager(db_manager=mock_db_manager)
    yield manager

    # Clean up
    SettingsManager.reset_instance()


class TestSettingsSchema:
    """Test SETTINGS_SCHEMA definition."""

    def test_schema_has_19_settings(self):
        """Test schema contains all 19 settings."""
        assert len(SETTINGS_SCHEMA) == 19

    def test_schema_categories(self):
        """Test schema organizes settings into 5 categories."""
        categories = set(s['category'] for s in SETTINGS_SCHEMA.values())
        assert categories == {'general', 'ai_model', 'performance', 'privacy', 'advanced'}

    def test_schema_general_settings(self):
        """Test general category has 4 settings."""
        general = [k for k, v in SETTINGS_SCHEMA.items() if v['category'] == 'general']
        assert len(general) == 4
        assert 'theme' in general
        assert 'startup_behavior' in general
        assert 'show_notifications' in general
        assert 'minimize_to_tray' in general

    def test_schema_ai_model_settings(self):
        """Test ai_model category has 4 settings."""
        ai_model = [k for k, v in SETTINGS_SCHEMA.items() if v['category'] == 'ai_model']
        assert len(ai_model) == 4

    def test_schema_performance_settings(self):
        """Test performance category has 4 settings."""
        performance = [k for k, v in SETTINGS_SCHEMA.items() if v['category'] == 'performance']
        assert len(performance) == 4

    def test_schema_privacy_settings(self):
        """Test privacy category has 3 settings."""
        privacy = [k for k, v in SETTINGS_SCHEMA.items() if v['category'] == 'privacy']
        assert len(privacy) == 3

    def test_schema_advanced_settings(self):
        """Test advanced category has 4 settings."""
        advanced = [k for k, v in SETTINGS_SCHEMA.items() if v['category'] == 'advanced']
        assert len(advanced) == 4

    def test_all_settings_have_required_fields(self):
        """Test all settings have required schema fields."""
        for key, schema in SETTINGS_SCHEMA.items():
            assert 'default' in schema
            assert 'type' in schema
            assert 'category' in schema
            assert 'restart_required' in schema


class TestSingletonPattern:
    """Test SettingsManager singleton pattern."""

    def test_get_instance_returns_singleton(self, mock_db_manager):
        """Test get_instance returns same instance."""
        SettingsManager.reset_instance()

        instance1 = SettingsManager.get_instance(mock_db_manager)
        instance2 = SettingsManager.get_instance(mock_db_manager)

        assert instance1 is instance2

        SettingsManager.reset_instance()

    def test_singleton_thread_safe(self, mock_db_manager):
        """Test singleton is thread-safe."""
        SettingsManager.reset_instance()

        instances = []

        def create_instance():
            instances.append(SettingsManager.get_instance(mock_db_manager))

        threads = [threading.Thread(target=create_instance) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All instances should be the same
        assert all(inst is instances[0] for inst in instances)

        SettingsManager.reset_instance()


class TestLoadSettings:
    """Test load_settings method."""

    def test_load_settings_returns_all_19_settings(self, settings_manager):
        """Test load_settings returns dict with 19 settings."""
        settings = settings_manager.load_settings()
        assert len(settings) == 19

    def test_load_settings_uses_defaults_on_first_run(self, settings_manager):
        """Test first run loads default values."""
        settings = settings_manager.load_settings()

        assert settings['theme'] == 'dark'
        assert settings['model'] == 'llama3:8b'
        assert settings['batch_size'] == 5
        assert settings['enable_telemetry'] is False

    def test_load_settings_from_database(self, mock_db_manager):
        """Test loading existing settings from database."""
        mock_db_manager.get_preference.side_effect = lambda key: {
            'theme': 'light',
            'batch_size': 10
        }.get(key, None)

        manager = SettingsManager(db_manager=mock_db_manager)
        settings = manager.load_settings()

        assert settings['theme'] == 'light'
        assert settings['batch_size'] == 10

        SettingsManager.reset_instance()

    def test_load_settings_fallback_to_defaults(self, mock_db_manager):
        """Test fallback to defaults when database value missing."""
        mock_db_manager.get_preference.return_value = None

        manager = SettingsManager(db_manager=mock_db_manager)
        settings = manager.load_settings()

        # Should use schema defaults
        assert settings['temperature'] == 0.7
        assert settings['cache_size_mb'] == 500

        SettingsManager.reset_instance()


class TestSaveSettings:
    """Test save_settings method."""

    def test_save_settings_to_database(self, settings_manager, mock_db_manager):
        """Test settings are saved to database."""
        settings = {'theme': 'light', 'batch_size': 10}

        settings_manager.save_settings(settings)

        # Should call set_preference for each setting
        assert mock_db_manager.set_preference.call_count >= 2

    def test_save_settings_validates_first(self, settings_manager):
        """Test validation occurs before saving."""
        invalid_settings = {'theme': 'invalid_theme'}

        with pytest.raises(SettingsValidationError):
            settings_manager.save_settings(invalid_settings)

    def test_save_settings_updates_cached_values(self, settings_manager):
        """Test saved settings update internal cache."""
        settings_manager.save_settings({'theme': 'light'})

        assert settings_manager.get_setting('theme') == 'light'

    def test_save_settings_notifies_observers(self, settings_manager):
        """Test saving settings triggers observer notifications."""
        callback = Mock()
        settings_manager.subscribe('theme', callback)

        settings_manager.save_settings({'theme': 'light'})

        callback.assert_called_once_with('light')

    def test_save_settings_ignores_unknown_keys(self, settings_manager):
        """Test unknown setting keys are ignored."""
        settings = {'unknown_key': 'value', 'theme': 'dark'}

        # Should not raise error
        settings_manager.save_settings(settings)


class TestGetSetting:
    """Test get_setting method."""

    def test_get_setting_retrieves_value(self, settings_manager):
        """Test getting a single setting value."""
        value = settings_manager.get_setting('theme')
        assert value == 'dark'  # Default value

    def test_get_setting_after_update(self, settings_manager):
        """Test getting updated value."""
        settings_manager.set_setting('theme', 'light')

        value = settings_manager.get_setting('theme')
        assert value == 'light'

    def test_get_setting_with_default(self, settings_manager):
        """Test get_setting returns default for unknown key."""
        value = settings_manager.get_setting('unknown_key', 'default')
        assert value == 'default'


class TestSetSetting:
    """Test set_setting method."""

    def test_set_setting_updates_value(self, settings_manager):
        """Test setting a single value."""
        settings_manager.set_setting('batch_size', 10)

        assert settings_manager.get_setting('batch_size') == 10

    def test_set_setting_validates(self, settings_manager):
        """Test set_setting validates value."""
        with pytest.raises(SettingsValidationError):
            settings_manager.set_setting('batch_size', 25)  # Out of range

    def test_set_setting_notifies_observers(self, settings_manager):
        """Test set_setting triggers observer notification."""
        callback = Mock()
        settings_manager.subscribe('temperature', callback)

        settings_manager.set_setting('temperature', 0.5)

        callback.assert_called_once_with(0.5)

    def test_set_setting_unknown_key_raises_error(self, settings_manager):
        """Test setting unknown key raises error."""
        with pytest.raises(SettingsValidationError):
            settings_manager.set_setting('unknown_key', 'value')


class TestResetToDefaults:
    """Test reset_to_defaults method."""

    def test_reset_to_defaults_restores_all_settings(self, settings_manager):
        """Test reset restores all 19 default values."""
        # Change some settings
        settings_manager.set_setting('theme', 'light')
        settings_manager.set_setting('batch_size', 15)

        # Reset
        settings_manager.reset_to_defaults()

        # Verify defaults restored
        assert settings_manager.get_setting('theme') == 'dark'
        assert settings_manager.get_setting('batch_size') == 5


class TestValidation:
    """Test settings validation."""

    def test_validate_temperature_range(self, settings_manager):
        """Test temperature range validation (0.0-1.0)."""
        # Valid
        assert settings_manager.validate_setting('temperature', 0.5) is None
        assert settings_manager.validate_setting('temperature', 0.0) is None
        assert settings_manager.validate_setting('temperature', 1.0) is None

        # Invalid
        assert settings_manager.validate_setting('temperature', 1.5) is not None
        assert settings_manager.validate_setting('temperature', -0.1) is not None

    def test_validate_batch_size_range(self, settings_manager):
        """Test batch size range validation (1-20)."""
        # Valid
        assert settings_manager.validate_setting('batch_size', 10) is None
        assert settings_manager.validate_setting('batch_size', 1) is None
        assert settings_manager.validate_setting('batch_size', 20) is None

        # Invalid
        assert settings_manager.validate_setting('batch_size', 25) is not None
        assert settings_manager.validate_setting('batch_size', 0) is not None

    def test_validate_cache_size_range(self, settings_manager):
        """Test cache size range validation (100-5000)."""
        # Valid
        assert settings_manager.validate_setting('cache_size_mb', 500) is None

        # Invalid
        assert settings_manager.validate_setting('cache_size_mb', 50) is not None
        assert settings_manager.validate_setting('cache_size_mb', 6000) is not None

    def test_validate_theme_enum(self, settings_manager):
        """Test theme enum validation (dark/light)."""
        # Valid
        assert settings_manager.validate_setting('theme', 'dark') is None
        assert settings_manager.validate_setting('theme', 'light') is None

        # Invalid
        assert settings_manager.validate_setting('theme', 'blue') is not None

    def test_validate_log_level_enum(self, settings_manager):
        """Test log level enum validation."""
        # Valid
        assert settings_manager.validate_setting('log_level', 'DEBUG') is None
        assert settings_manager.validate_setting('log_level', 'INFO') is None

        # Invalid
        assert settings_manager.validate_setting('log_level', 'TRACE') is not None

    def test_validate_type_int(self, settings_manager):
        """Test integer type validation."""
        # Valid
        assert settings_manager.validate_setting('batch_size', 5) is None

        # Invalid
        assert settings_manager.validate_setting('batch_size', "5") is not None
        assert settings_manager.validate_setting('batch_size', 5.5) is not None

    def test_validate_type_bool(self, settings_manager):
        """Test boolean type validation."""
        # Valid
        assert settings_manager.validate_setting('use_gpu', True) is None
        assert settings_manager.validate_setting('use_gpu', False) is None

        # Invalid
        assert settings_manager.validate_setting('use_gpu', 1) is not None
        assert settings_manager.validate_setting('use_gpu', "true") is not None

    def test_validate_unknown_setting(self, settings_manager):
        """Test validating unknown setting returns error."""
        error = settings_manager.validate_setting('unknown_key', 'value')
        assert error is not None


class TestObserverPattern:
    """Test observer pattern for change notifications."""

    def test_subscribe_adds_observer(self, settings_manager):
        """Test subscribing to setting changes."""
        callback = Mock()

        settings_manager.subscribe('theme', callback)

        # Should be in observers
        assert 'theme' in settings_manager._observers
        assert callback in settings_manager._observers['theme']

    def test_unsubscribe_removes_observer(self, settings_manager):
        """Test unsubscribing from setting changes."""
        callback = Mock()

        settings_manager.subscribe('theme', callback)
        settings_manager.unsubscribe('theme', callback)

        # Should be removed
        assert callback not in settings_manager._observers.get('theme', [])

    def test_observer_receives_new_value(self, settings_manager):
        """Test observer callback receives new value."""
        callback = Mock()
        settings_manager.subscribe('batch_size', callback)

        settings_manager.set_setting('batch_size', 15)

        callback.assert_called_once_with(15)

    def test_multiple_observers_all_notified(self, settings_manager):
        """Test all observers are notified."""
        callback1 = Mock()
        callback2 = Mock()
        callback3 = Mock()

        settings_manager.subscribe('theme', callback1)
        settings_manager.subscribe('theme', callback2)
        settings_manager.subscribe('theme', callback3)

        settings_manager.set_setting('theme', 'light')

        callback1.assert_called_once_with('light')
        callback2.assert_called_once_with('light')
        callback3.assert_called_once_with('light')

    def test_observer_exception_does_not_crash(self, settings_manager):
        """Test observer exception doesn't crash SettingsManager."""
        def failing_callback(value):
            raise Exception("Observer error")

        settings_manager.subscribe('theme', failing_callback)

        # Should not raise
        settings_manager.set_setting('theme', 'light')

    def test_no_notification_if_value_unchanged(self, settings_manager):
        """Test no notification if value doesn't change."""
        callback = Mock()
        settings_manager.subscribe('theme', callback)

        # Set to same value
        settings_manager.save_settings({'theme': 'dark'})

        # Should not be called (value already 'dark')
        callback.assert_not_called()


class TestHelperMethods:
    """Test helper methods."""

    def test_get_settings_by_category(self, settings_manager):
        """Test getting settings by category."""
        general = settings_manager.get_settings_by_category('general')

        assert len(general) == 4
        assert 'theme' in general
        assert 'startup_behavior' in general

    def test_get_restart_required_settings(self, settings_manager):
        """Test getting restart-required settings."""
        restart_required = settings_manager.get_restart_required_settings()

        # Should include: model, startup_behavior, use_gpu, database_path
        assert 'model' in restart_required
        assert 'startup_behavior' in restart_required
        assert 'use_gpu' in restart_required
        assert 'database_path' in restart_required

        # Should not include immediate settings
        assert 'theme' not in restart_required


class TestThreadSafety:
    """Test thread-safety of SettingsManager."""

    def test_concurrent_get_setting(self, settings_manager):
        """Test concurrent get_setting calls."""
        results = []

        def get_theme():
            results.append(settings_manager.get_setting('theme'))

        threads = [threading.Thread(target=get_theme) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All results should be consistent
        assert all(r == results[0] for r in results)

    def test_concurrent_set_setting(self, settings_manager):
        """Test concurrent set_setting calls."""
        def set_batch_size(value):
            try:
                settings_manager.set_setting('batch_size', value)
            except:
                pass  # Some may fail validation

        threads = [threading.Thread(target=set_batch_size, args=(i,)) for i in range(5, 10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Final value should be valid
        final = settings_manager.get_setting('batch_size')
        assert 1 <= final <= 20


class TestYamlExport:
    """Test YAML export functionality."""

    def test_export_to_yaml_creates_file(self, settings_manager, tmp_path):
        """Test export creates YAML file."""
        yaml_path = tmp_path / "test-settings.yaml"

        settings_manager.export_to_yaml(str(yaml_path))

        assert yaml_path.exists()

    def test_export_yaml_organized_by_category(self, settings_manager, tmp_path):
        """Test YAML file organized by category."""
        yaml_path = tmp_path / "test-settings.yaml"

        settings_manager.export_to_yaml(str(yaml_path))

        content = yaml_path.read_text()
        assert 'general:' in content
        assert 'ai_model:' in content
        assert 'performance:' in content
        assert 'privacy:' in content
        assert 'advanced:' in content

    def test_export_yaml_includes_comments(self, settings_manager, tmp_path):
        """Test YAML includes descriptive comments."""
        yaml_path = tmp_path / "test-settings.yaml"

        settings_manager.export_to_yaml(str(yaml_path))

        content = yaml_path.read_text()
        assert '# UI theme' in content
        assert '# MailMind User Settings' in content

    def test_export_yaml_preserves_all_19_settings(self, settings_manager, tmp_path):
        """Test all 19 settings exported."""
        yaml_path = tmp_path / "test-settings.yaml"

        settings_manager.export_to_yaml(str(yaml_path))

        content = yaml_path.read_text()
        # Check some key settings
        assert 'theme:' in content
        assert 'model:' in content
        assert 'batch_size:' in content

    def test_export_yaml_creates_parent_directory(self, settings_manager, tmp_path):
        """Test export creates parent directories if needed."""
        yaml_path = tmp_path / "config" / "test-settings.yaml"

        settings_manager.export_to_yaml(str(yaml_path))

        assert yaml_path.exists()


class TestYamlImport:
    """Test YAML import functionality."""

    def test_load_from_yaml_imports_settings(self, settings_manager, tmp_path):
        """Test loading settings from YAML file."""
        yaml_path = tmp_path / "test-settings.yaml"

        # Create test YAML
        yaml_content = """
general:
  theme: light
  show_notifications: false

ai_model:
  temperature: 0.5
  model: mistral:7b
"""
        yaml_path.write_text(yaml_content)

        settings_manager.load_from_yaml(str(yaml_path))

        assert settings_manager.get_setting('theme') == 'light'
        assert settings_manager.get_setting('show_notifications') is False
        assert settings_manager.get_setting('temperature') == 0.5

    def test_load_from_yaml_validates_settings(self, settings_manager, tmp_path):
        """Test YAML import validates settings."""
        yaml_path = tmp_path / "test-settings.yaml"

        # Create YAML with invalid setting
        yaml_content = """
general:
  theme: invalid_theme
"""
        yaml_path.write_text(yaml_content)

        with pytest.raises(SettingsValidationError):
            settings_manager.load_from_yaml(str(yaml_path))

    def test_load_from_yaml_file_not_found(self, settings_manager, tmp_path):
        """Test loading from non-existent file raises error."""
        yaml_path = tmp_path / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError):
            settings_manager.load_from_yaml(str(yaml_path))

    def test_load_from_yaml_handles_malformed_yaml(self, settings_manager, tmp_path):
        """Test malformed YAML raises error."""
        yaml_path = tmp_path / "test-settings.yaml"

        # Create malformed YAML
        yaml_content = """
general:
  theme: light
    invalid indentation
"""
        yaml_path.write_text(yaml_content)

        # Should raise YAML error
        with pytest.raises(Exception):  # yaml.YAMLError
            settings_manager.load_from_yaml(str(yaml_path))

    def test_export_import_round_trip(self, settings_manager, tmp_path):
        """Test export then import preserves settings."""
        yaml_path = tmp_path / "test-settings.yaml"

        # Set some custom values
        settings_manager.set_setting('theme', 'light')
        settings_manager.set_setting('batch_size', 15)

        # Export
        settings_manager.export_to_yaml(str(yaml_path))

        # Reset to defaults
        settings_manager.reset_to_defaults()
        assert settings_manager.get_setting('theme') == 'dark'

        # Import
        settings_manager.load_from_yaml(str(yaml_path))

        # Should restore custom values
        assert settings_manager.get_setting('theme') == 'light'
        assert settings_manager.get_setting('batch_size') == 15


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_settings_dict(self, settings_manager):
        """Test saving empty settings dict."""
        # Should not crash
        settings_manager.save_settings({})

    def test_none_value_validation(self, settings_manager):
        """Test validating None value."""
        # None is invalid for all settings
        error = settings_manager.validate_setting('theme', None)
        assert error is not None

    def test_validate_multiple_settings(self, settings_manager):
        """Test validating multiple settings at once."""
        settings = {
            'theme': 'dark',
            'batch_size': 10,
            'temperature': 0.7
        }

        errors = settings_manager.validate_settings(settings)
        assert len(errors) == 0

        invalid_settings = {
            'theme': 'invalid',
            'batch_size': 100
        }

        errors = settings_manager.validate_settings(invalid_settings)
        assert len(errors) == 2

    def test_load_settings_exception_handling(self, mock_db_manager):
        """Test load_settings handles database exceptions."""
        mock_db_manager.get_preference.side_effect = Exception("DB Error")

        manager = SettingsManager(db_manager=mock_db_manager)
        settings = manager.load_settings()

        # Should fall back to defaults
        assert len(settings) == 19
        assert settings['theme'] == 'dark'

        SettingsManager.reset_instance()

    def test_save_settings_exception_handling(self, settings_manager, mock_db_manager):
        """Test save_settings handles database exceptions."""
        mock_db_manager.set_preference.side_effect = Exception("DB Error")

        with pytest.raises(Exception):
            settings_manager.save_settings({'theme': 'light'})
