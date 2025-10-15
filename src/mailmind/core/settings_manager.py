"""
Settings Manager for MailMind.

Provides centralized settings management with database persistence,
validation, observer pattern for change notifications, and YAML export/import.

Story 2.4: Settings & Configuration System
"""

import threading
import logging
from typing import Any, Dict, Optional, Callable, List
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)


# Complete settings schema with all 19 settings
SETTINGS_SCHEMA = {
    # General (4 settings)
    "theme": {
        "default": "dark",
        "type": "string",
        "category": "general",
        "validation": "enum:dark,light",
        "restart_required": False,
        "description": "UI theme: 'dark' or 'light'"
    },
    "startup_behavior": {
        "default": "normal",
        "type": "string",
        "category": "general",
        "validation": "enum:normal,minimized,tray",
        "restart_required": True,
        "description": "Startup behavior: 'normal', 'minimized', or 'tray'"
    },
    "show_notifications": {
        "default": True,
        "type": "bool",
        "category": "general",
        "validation": None,
        "restart_required": False,
        "description": "Show desktop notifications for email events"
    },
    "minimize_to_tray": {
        "default": False,
        "type": "bool",
        "category": "general",
        "validation": None,
        "restart_required": False,
        "description": "Minimize application to system tray"
    },

    # AI Model (4 settings)
    "model": {
        "default": "llama3:8b",
        "type": "string",
        "category": "ai_model",
        "validation": "enum:llama3:8b,llama3:13b,mistral:7b,phi3:mini",
        "restart_required": True,
        "description": "AI model: 'llama3:8b', 'llama3:13b', 'mistral:7b', 'phi3:mini' (restart required)"
    },
    "temperature": {
        "default": 0.7,
        "type": "float",
        "category": "ai_model",
        "validation": "range:0.0-1.0",
        "restart_required": False,
        "description": "Temperature (creativity): 0.0 (deterministic) to 1.0 (creative)"
    },
    "response_length_default": {
        "default": "Standard",
        "type": "string",
        "category": "ai_model",
        "validation": "enum:Brief,Standard,Detailed",
        "restart_required": False,
        "description": "Default response length: 'Brief', 'Standard', 'Detailed'"
    },
    "response_tone_default": {
        "default": "Professional",
        "type": "string",
        "category": "ai_model",
        "validation": "enum:Professional,Friendly,Formal,Casual",
        "restart_required": False,
        "description": "Default response tone: 'Professional', 'Friendly', 'Formal', 'Casual'"
    },

    # Performance (4 settings)
    "batch_size": {
        "default": 5,
        "type": "int",
        "category": "performance",
        "validation": "range:1-20",
        "restart_required": False,
        "description": "Batch processing size: 1-20 emails"
    },
    "cache_size_mb": {
        "default": 500,
        "type": "int",
        "category": "performance",
        "validation": "range:100-5000",
        "restart_required": False,
        "description": "Cache size limit in MB: 100-5000"
    },
    "use_gpu": {
        "default": False,
        "type": "bool",
        "category": "performance",
        "validation": None,
        "restart_required": True,
        "description": "Use GPU acceleration if available (restart required)"
    },
    "max_concurrent": {
        "default": 3,
        "type": "int",
        "category": "performance",
        "validation": "range:1-5",
        "restart_required": False,
        "description": "Maximum concurrent analyses: 1-5"
    },

    # Privacy (3 settings)
    "enable_telemetry": {
        "default": False,
        "type": "bool",
        "category": "privacy",
        "validation": None,
        "restart_required": False,
        "description": "Send anonymous usage statistics (default: off)"
    },
    "enable_crash_reports": {
        "default": True,
        "type": "bool",
        "category": "privacy",
        "validation": None,
        "restart_required": False,
        "description": "Send crash reports to help improve MailMind"
    },
    "log_level": {
        "default": "INFO",
        "type": "string",
        "category": "privacy",
        "validation": "enum:DEBUG,INFO,WARNING,ERROR",
        "restart_required": False,
        "description": "Logging level: 'DEBUG', 'INFO', 'WARNING', 'ERROR'"
    },

    # Advanced (4 settings)
    "database_path": {
        "default": "data/mailmind.db",
        "type": "string",
        "category": "advanced",
        "validation": None,
        "restart_required": True,
        "description": "Database file location (restart required)"
    },
    "debug_mode": {
        "default": False,
        "type": "bool",
        "category": "advanced",
        "validation": None,
        "restart_required": False,
        "description": "Enable debug mode (verbose logging)"
    },
    "auto_backup": {
        "default": True,
        "type": "bool",
        "category": "advanced",
        "validation": None,
        "restart_required": False,
        "description": "Enable automatic database backups"
    },
    "backup_frequency_hours": {
        "default": 24,
        "type": "int",
        "category": "advanced",
        "validation": "range:1-168",
        "restart_required": False,
        "description": "Backup frequency in hours: 1-168 (1 week)"
    }
}


class SettingsValidationError(Exception):
    """Raised when a setting value fails validation."""
    pass


class SettingsManager:
    """
    Centralized settings manager with database persistence, validation, and observer pattern.

    Implements singleton pattern for global access and thread-safe operations.
    Integrates with DatabaseManager for persistence and SettingsDialog for UI.

    Story 2.4 AC1, AC3, AC6, AC8
    """

    _instance: Optional['SettingsManager'] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self, db_manager=None):
        """
        Initialize SettingsManager. Use get_instance() for singleton access.

        Args:
            db_manager: Optional DatabaseManager instance (for testing)
        """
        self._db_manager = db_manager
        self._settings: Dict[str, Any] = {}
        self._observers: Dict[str, List[Callable]] = {}
        self._settings_lock = threading.Lock()

        # Load settings on initialization
        self._settings = self.load_settings()

        logger.info("SettingsManager initialized with %d settings", len(self._settings))

    @classmethod
    def get_instance(cls, db_manager=None) -> 'SettingsManager':
        """
        Get singleton instance of SettingsManager (thread-safe).

        Args:
            db_manager: Optional DatabaseManager instance (for testing)

        Returns:
            SettingsManager singleton instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(db_manager)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Reset singleton instance (for testing only)."""
        with cls._lock:
            cls._instance = None

    def _get_db_manager(self):
        """Get DatabaseManager instance (lazy loading)."""
        if self._db_manager is None:
            from mailmind.database import DatabaseManager
            self._db_manager = DatabaseManager.get_instance()
        return self._db_manager

    def load_settings(self) -> Dict[str, Any]:
        """
        Load settings from database with fallback to defaults.

        Returns:
            Dict of all 19 settings with values

        Story 2.4 AC1, AC3
        """
        settings = {}
        db = self._get_db_manager()

        for key, schema in SETTINGS_SCHEMA.items():
            try:
                # Try to load from database
                value = db.get_preference(key)
                if value is not None:
                    settings[key] = value
                else:
                    # Use default if not in database
                    settings[key] = schema['default']
                    logger.debug(f"Using default for setting '{key}': {schema['default']}")
            except Exception as e:
                # Fall back to default on any error
                logger.warning(f"Error loading setting '{key}': {e}. Using default.")
                settings[key] = schema['default']

        logger.info(f"Loaded {len(settings)} settings from database")
        return settings

    def save_settings(self, settings: Dict[str, Any]) -> None:
        """
        Save settings to database with validation.

        Args:
            settings: Dict of settings to save

        Raises:
            SettingsValidationError: If any setting fails validation

        Story 2.4 AC1, AC3, AC6
        """
        # Validate all settings first
        errors = []
        for key, value in settings.items():
            if key not in SETTINGS_SCHEMA:
                logger.warning(f"Unknown setting key '{key}' - ignoring")
                continue

            error = self.validate_setting(key, value)
            if error:
                errors.append(error)

        if errors:
            raise SettingsValidationError("; ".join(errors))

        # Save to database
        db = self._get_db_manager()

        with self._settings_lock:
            for key, value in settings.items():
                if key not in SETTINGS_SCHEMA:
                    continue

                schema = SETTINGS_SCHEMA[key]

                try:
                    # Store in database with metadata
                    db.set_preference(key, value)

                    # Update cached value
                    old_value = self._settings.get(key)
                    self._settings[key] = value

                    # Notify observers if value changed
                    if old_value != value:
                        self._notify_observers(key, value)

                except Exception as e:
                    logger.error(f"Failed to save setting '{key}': {e}")
                    raise

        logger.info(f"Saved {len(settings)} settings to database")

    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a single setting value.

        Args:
            key: Setting key
            default: Default value if not found

        Returns:
            Setting value or default

        Story 2.4 AC3
        """
        with self._settings_lock:
            if key in self._settings:
                return self._settings[key]
            elif key in SETTINGS_SCHEMA:
                return SETTINGS_SCHEMA[key]['default']
            else:
                return default

    def set_setting(self, key: str, value: Any) -> None:
        """
        Set a single setting value with validation.

        Args:
            key: Setting key
            value: New value

        Raises:
            SettingsValidationError: If validation fails

        Story 2.4 AC3, AC6
        """
        if key not in SETTINGS_SCHEMA:
            raise SettingsValidationError(f"Unknown setting key: {key}")

        # Validate
        error = self.validate_setting(key, value)
        if error:
            raise SettingsValidationError(error)

        # Save to database
        db = self._get_db_manager()

        with self._settings_lock:
            old_value = self._settings.get(key)

            try:
                db.set_preference(key, value)
                self._settings[key] = value

                # Notify observers if value changed
                if old_value != value:
                    self._notify_observers(key, value)

            except Exception as e:
                logger.error(f"Failed to set setting '{key}': {e}")
                raise

    def reset_to_defaults(self) -> None:
        """
        Reset all settings to default values.

        Story 2.4 AC3, AC7
        """
        defaults = {key: schema['default'] for key, schema in SETTINGS_SCHEMA.items()}
        self.save_settings(defaults)
        logger.info("Reset all settings to defaults")

    def validate_setting(self, key: str, value: Any) -> Optional[str]:
        """
        Validate a setting value.

        Args:
            key: Setting key
            value: Value to validate

        Returns:
            Error message if invalid, None if valid

        Story 2.4 AC6
        """
        if key not in SETTINGS_SCHEMA:
            return f"Unknown setting: {key}"

        schema = SETTINGS_SCHEMA[key]

        # Type validation
        expected_type = schema['type']

        if expected_type == 'int':
            if not isinstance(value, int) or isinstance(value, bool):
                return f"{key} must be an integer, got {type(value).__name__}"
        elif expected_type == 'float':
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                return f"{key} must be a number, got {type(value).__name__}"
        elif expected_type == 'bool':
            if not isinstance(value, bool):
                return f"{key} must be a boolean, got {type(value).__name__}"
        elif expected_type == 'string':
            if not isinstance(value, str):
                return f"{key} must be a string, got {type(value).__name__}"

        # Validation rules
        validation = schema.get('validation')
        if validation:
            if validation.startswith('enum:'):
                allowed = validation.split(':', 1)[1].split(',')
                if value not in allowed:
                    return f"{key} must be one of: {', '.join(allowed)}"

            elif validation.startswith('range:'):
                range_str = validation.split(':', 1)[1]
                try:
                    min_val, max_val = map(float, range_str.split('-'))
                    if not (min_val <= value <= max_val):
                        return f"{key} must be between {min_val} and {max_val}"
                except ValueError:
                    logger.error(f"Invalid range format in schema for {key}: {validation}")

        return None  # Valid

    def validate_settings(self, settings: Dict[str, Any]) -> List[str]:
        """
        Validate multiple settings.

        Args:
            settings: Dict of settings to validate

        Returns:
            List of error messages (empty if all valid)
        """
        errors = []
        for key, value in settings.items():
            if key not in SETTINGS_SCHEMA:
                continue
            error = self.validate_setting(key, value)
            if error:
                errors.append(error)
        return errors

    def subscribe(self, setting_key: str, callback: Callable[[Any], None]) -> None:
        """
        Subscribe to setting change notifications.

        Args:
            setting_key: Setting to observe
            callback: Function to call when setting changes (receives new value)

        Story 2.4 AC8
        """
        with self._settings_lock:
            if setting_key not in self._observers:
                self._observers[setting_key] = []
            if callback not in self._observers[setting_key]:
                self._observers[setting_key].append(callback)
                logger.debug(f"Added observer for setting '{setting_key}'")

    def unsubscribe(self, setting_key: str, callback: Callable[[Any], None]) -> None:
        """
        Unsubscribe from setting change notifications.

        Args:
            setting_key: Setting to stop observing
            callback: Callback to remove

        Story 2.4 AC8
        """
        with self._settings_lock:
            if setting_key in self._observers:
                if callback in self._observers[setting_key]:
                    self._observers[setting_key].remove(callback)
                    logger.debug(f"Removed observer for setting '{setting_key}'")

    def _notify_observers(self, setting_key: str, new_value: Any) -> None:
        """
        Notify observers of setting change.

        Args:
            setting_key: Setting that changed
            new_value: New value

        Story 2.4 AC8
        """
        if setting_key in self._observers:
            for callback in self._observers[setting_key]:
                try:
                    callback(new_value)
                except Exception as e:
                    logger.error(f"Observer callback failed for '{setting_key}': {e}")

    def get_settings_by_category(self, category: str) -> Dict[str, Any]:
        """
        Get all settings for a specific category.

        Args:
            category: Category name (general, ai_model, performance, privacy, advanced)

        Returns:
            Dict of settings in that category
        """
        with self._settings_lock:
            return {
                key: self._settings[key]
                for key, schema in SETTINGS_SCHEMA.items()
                if schema['category'] == category and key in self._settings
            }

    def get_restart_required_settings(self) -> List[str]:
        """
        Get list of settings that require restart.

        Returns:
            List of setting keys that require restart

        Story 2.4 AC5
        """
        return [
            key for key, schema in SETTINGS_SCHEMA.items()
            if schema.get('restart_required', False)
        ]

    def export_to_yaml(self, filepath: str) -> None:
        """
        Export settings to YAML file.

        Args:
            filepath: Path to YAML file

        Story 2.4 AC2, AC9
        """
        # Organize settings by category
        settings_by_category = {}

        for key, value in self._settings.items():
            schema = SETTINGS_SCHEMA[key]
            category = schema['category']

            if category not in settings_by_category:
                settings_by_category[category] = {}

            settings_by_category[category][key] = value

        # Create YAML content with comments
        yaml_content = "# MailMind User Settings\n"
        yaml_content += "# Generated by SettingsManager\n\n"

        for category in ['general', 'ai_model', 'performance', 'privacy', 'advanced']:
            if category not in settings_by_category:
                continue

            yaml_content += f"# {category.replace('_', ' ').title()} Settings\n"
            yaml_content += f"{category}:\n"

            for key, value in settings_by_category[category].items():
                schema = SETTINGS_SCHEMA[key]
                description = schema.get('description', '')
                if description:
                    yaml_content += f"  # {description}\n"

                # Format value
                if isinstance(value, bool):
                    value_str = str(value).lower()
                elif isinstance(value, str):
                    value_str = value
                else:
                    value_str = str(value)

                yaml_content += f"  {key}: {value_str}\n"

            yaml_content += "\n"

        # Write to file
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(yaml_content)

        logger.info(f"Exported settings to {filepath}")

    def load_from_yaml(self, filepath: str) -> None:
        """
        Load settings from YAML file and save to database.

        Args:
            filepath: Path to YAML file

        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML parsing fails

        Story 2.4 AC2, AC9
        """
        if not Path(filepath).exists():
            raise FileNotFoundError(f"YAML file not found: {filepath}")

        try:
            with open(filepath, 'r') as f:
                yaml_data = yaml.safe_load(f)

            if not yaml_data:
                logger.warning(f"Empty YAML file: {filepath}")
                return

            # Flatten category structure
            settings_to_load = {}
            for category, settings in yaml_data.items():
                if isinstance(settings, dict):
                    settings_to_load.update(settings)

            # Validate and save
            if settings_to_load:
                self.save_settings(settings_to_load)
                logger.info(f"Loaded {len(settings_to_load)} settings from {filepath}")

        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML file {filepath}: {e}")
            raise
