# Story 2.4: Settings & Configuration System

**Status:** Ready
**Epic:** 2 - Desktop Application & User Experience
**Story Points:** 5
**Priority:** P1 (Important)
**Created:** 2025-10-14

---

## Story

As a user,
I want a comprehensive settings system to customize MailMind's behavior,
so that the application works according to my preferences and all settings persist across sessions.

## Context

Story 2.4 implements the settings persistence and configuration management layer that integrates the SettingsDialog UI component (Story 2.3) with the DatabaseManager's user_preferences table (Story 2.2). While the UI component already exists with 19 settings across 5 tabs, this story adds the backend logic to load, save, and apply settings with validation and proper defaults.

**Why This Story Is Critical:**
- Connects UI components to persistent storage for stateful application behavior
- Enables user customization of AI model parameters, performance options, and privacy controls
- Provides YAML configuration file backup for power users
- Implements immediate setting application without restart where possible
- Establishes patterns for settings validation and migration

**Integration with Completed Stories:**
- **Story 2.2 (DatabaseManager)**: Uses `user_preferences` table for settings persistence
- **Story 2.3 (SettingsDialog)**: Provides the UI component for settings management - this story adds the backend integration
- **Story 1.1 (OllamaManager)**: Will read AI model settings (model selection, temperature)
- **Story 1.6 (PerformanceTracker)**: Will read performance settings (batch size, GPU toggle)

---

## Acceptance Criteria

### AC1: Settings Storage in user_preferences Table
- ✅ All 19 settings stored in DatabaseManager's `user_preferences` table
- ✅ Settings organized by category: general (4), ai_model (4), performance (4), privacy (3), advanced (4)
- ✅ Each setting has: key, value, default_value, value_type, category
- ✅ Value types properly enforced: string, int, float, bool, json
- ✅ Settings loaded on application startup with defaults if not found

### AC2: YAML Config File Backup
- ✅ Export settings to YAML file: `config/user-settings.yaml`
- ✅ YAML file organized by category matching Settings Dialog tabs
- ✅ Load settings from YAML file if database unavailable
- ✅ Manual YAML edits sync to database on next startup
- ✅ YAML file includes comments describing each setting

### AC3: Settings Manager Class
- ✅ Create centralized `SettingsManager` class for all settings operations
- ✅ Methods: `load_settings()`, `save_settings(dict)`, `get_setting(key)`, `set_setting(key, value)`, `reset_to_defaults()`
- ✅ Singleton pattern for global access: `SettingsManager.get_instance()`
- ✅ Thread-safe operations for concurrent access
- ✅ Validation of setting values before saving (type checking, range validation)

### AC4: Integration with SettingsDialog UI
- ✅ SettingsDialog loads current settings from SettingsManager on open
- ✅ Save button writes settings via `SettingsManager.save_settings()`
- ✅ Reset to Defaults button calls `SettingsManager.reset_to_defaults()`
- ✅ Settings changes propagated to application components via observer pattern
- ✅ Invalid settings rejected with user-friendly error messages

### AC5: Immediate Settings Application
- ✅ Theme changes apply immediately (dark/light mode switch)
- ✅ Model selection requires restart (display warning in UI)
- ✅ Performance settings (batch size, GPU toggle) apply to next operation
- ✅ Privacy settings (telemetry, logging level) apply immediately
- ✅ Database path changes require restart (display warning)

### AC6: Settings Validation
- ✅ Temperature range: 0.0 to 1.0 (float)
- ✅ Batch size range: 1 to 20 (int)
- ✅ Cache size: 100 to 5000 MB (int)
- ✅ Max concurrent: 1 to 5 (int)
- ✅ Backup frequency: 1 to 168 hours (int)
- ✅ Enum validation: theme (dark/light), startup_behavior (normal/minimized/tray), log_level (DEBUG/INFO/WARNING/ERROR)

### AC7: Default Settings
- ✅ All settings have documented default values
- ✅ Defaults match those specified in Epic 2 (epic-stories.md lines 399-421)
- ✅ First-run initialization populates database with defaults
- ✅ Reset to Defaults option available in Settings Dialog

### AC8: Settings Change Notifications
- ✅ Observer pattern for components to subscribe to setting changes
- ✅ Observers receive callbacks when specific settings change
- ✅ Example: ThemeManager subscribes to "theme" setting
- ✅ Example: OllamaManager subscribes to "model" and "temperature" settings

### AC9: Settings Export/Import
- ✅ Export current settings to timestamped YAML file: `settings-backup-2025-10-14.yaml`
- ✅ Import settings from YAML file with validation
- ✅ Merge imported settings with existing (prompt for conflicts)
- ✅ Export/Import accessible from Settings Dialog Advanced tab

---

## Tasks / Subtasks

### Task 1: SettingsManager Core Implementation (AC1, AC3, AC6)
- [ ] Create `src/mailmind/core/settings_manager.py`
- [ ] Implement `SettingsManager` class with singleton pattern
- [ ] Define all 19 settings with metadata (key, default, type, category, validation rules)
- [ ] Implement `load_settings()` - read from database or use defaults
- [ ] Implement `save_settings(dict)` - validate and write to database
- [ ] Implement `get_setting(key)` - retrieve single setting value
- [ ] Implement `set_setting(key, value)` - validate and update setting
- [ ] Implement `reset_to_defaults()` - restore all defaults
- [ ] Add validation logic for each setting type (range checks, enum validation)
- [ ] Add thread-safety via locks for concurrent access
- [ ] Write unit tests for SettingsManager operations

### Task 2: Database Integration (AC1)
- [ ] Use DatabaseManager's `user_preferences` table for storage
- [ ] Implement CRUD operations via DatabaseManager
- [ ] Populate default settings on first run
- [ ] Handle setting retrieval with fallback to defaults
- [ ] Store setting metadata (category, value_type) in database
- [ ] Write integration tests with DatabaseManager

### Task 3: YAML Config File Support (AC2)
- [ ] Create `config/` directory for YAML files
- [ ] Implement YAML export: `export_to_yaml(filepath)` method
- [ ] Implement YAML import: `load_from_yaml(filepath)` method
- [ ] Generate commented YAML with setting descriptions
- [ ] Sync YAML changes to database on startup
- [ ] Handle YAML parsing errors gracefully
- [ ] Write unit tests for YAML export/import

### Task 4: SettingsDialog Integration (AC4)
- [ ] Update SettingsDialog to use SettingsManager
- [ ] Replace `_get_default_settings()` with `SettingsManager.load_settings()`
- [ ] Update `_on_save_clicked()` to call `SettingsManager.save_settings()`
- [ ] Update `_on_reset_clicked()` to call `SettingsManager.reset_to_defaults()`
- [ ] Add validation error handling with user-friendly messages
- [ ] Display toast notifications on successful save
- [ ] Write integration tests with SettingsDialog

### Task 5: Settings Change Notification System (AC8)
- [ ] Implement Observer pattern for settings changes
- [ ] Create `SettingChangeListener` interface
- [ ] Implement `subscribe(setting_key, callback)` method
- [ ] Implement `unsubscribe(setting_key, callback)` method
- [ ] Notify observers when settings change via `set_setting()` or `save_settings()`
- [ ] Add example observer: ThemeManager subscribes to "theme" setting
- [ ] Write unit tests for observer pattern

### Task 6: Immediate Settings Application (AC5)
- [ ] Identify settings requiring restart vs immediate application
- [ ] Implement immediate application for theme changes (ThemeManager.set_theme())
- [ ] Implement immediate application for log level (logging.setLevel())
- [ ] Display warning dialog for settings requiring restart
- [ ] Add "Restart Now" button for restart-required settings
- [ ] Write tests for immediate vs deferred application

### Task 7: Export/Import Feature (AC9)
- [ ] Add Export/Import buttons to Settings Dialog Advanced tab
- [ ] Implement timestamped export: `settings-backup-2025-10-14.yaml`
- [ ] Implement import with file picker dialog
- [ ] Validate imported settings (schema, types, ranges)
- [ ] Handle conflicts: prompt user to keep existing or use imported
- [ ] Show success/error messages after export/import
- [ ] Write tests for export/import with various scenarios

### Task 8: Component Integration Examples
- [ ] ThemeManager subscribes to "theme" setting
- [ ] OllamaManager subscribes to "model" and "temperature" settings
- [ ] BatchQueueManager subscribes to "batch_size" setting
- [ ] PerformanceTracker subscribes to "use_gpu" and "max_concurrent" settings
- [ ] StatusBar displays warning icon if settings require restart
- [ ] Write integration examples in `examples/settings_integration_demo.py`

### Task 9: Testing and Documentation
- [ ] Write comprehensive unit tests (target: >85% coverage)
- [ ] Write integration tests with DatabaseManager and SettingsDialog
- [ ] Test all 19 settings load/save correctly
- [ ] Test validation rejects invalid values
- [ ] Test observer notifications work correctly
- [ ] Create demo script: `examples/settings_demo.py`
- [ ] Document settings categories and validation rules
- [ ] Update README with settings management instructions
- [ ] Update CHANGELOG with Story 2.4 completion

---

## Dev Notes

### Settings Definition

**All 19 Settings with Metadata:**

```python
SETTINGS_SCHEMA = {
    # General (4 settings)
    "theme": {
        "default": "dark",
        "type": "string",
        "category": "general",
        "validation": "enum:dark,light",
        "restart_required": False
    },
    "startup_behavior": {
        "default": "normal",
        "type": "string",
        "category": "general",
        "validation": "enum:normal,minimized,tray",
        "restart_required": True
    },
    "show_notifications": {
        "default": True,
        "type": "bool",
        "category": "general",
        "validation": None,
        "restart_required": False
    },
    "minimize_to_tray": {
        "default": False,
        "type": "bool",
        "category": "general",
        "validation": None,
        "restart_required": False
    },

    # AI Model (4 settings)
    "model": {
        "default": "llama3:8b",
        "type": "string",
        "category": "ai_model",
        "validation": "enum:llama3:8b,llama3:13b,mistral:7b,phi3:mini",
        "restart_required": True
    },
    "temperature": {
        "default": 0.7,
        "type": "float",
        "category": "ai_model",
        "validation": "range:0.0-1.0",
        "restart_required": False
    },
    "response_length_default": {
        "default": "Standard",
        "type": "string",
        "category": "ai_model",
        "validation": "enum:Brief,Standard,Detailed",
        "restart_required": False
    },
    "response_tone_default": {
        "default": "Professional",
        "type": "string",
        "category": "ai_model",
        "validation": "enum:Professional,Friendly,Formal,Casual",
        "restart_required": False
    },

    # Performance (4 settings)
    "batch_size": {
        "default": 5,
        "type": "int",
        "category": "performance",
        "validation": "range:1-20",
        "restart_required": False
    },
    "cache_size_mb": {
        "default": 500,
        "type": "int",
        "category": "performance",
        "validation": "range:100-5000",
        "restart_required": False
    },
    "use_gpu": {
        "default": False,
        "type": "bool",
        "category": "performance",
        "validation": None,
        "restart_required": True
    },
    "max_concurrent": {
        "default": 3,
        "type": "int",
        "category": "performance",
        "validation": "range:1-5",
        "restart_required": False
    },

    # Privacy (3 settings)
    "enable_telemetry": {
        "default": False,
        "type": "bool",
        "category": "privacy",
        "validation": None,
        "restart_required": False
    },
    "enable_crash_reports": {
        "default": True,
        "type": "bool",
        "category": "privacy",
        "validation": None,
        "restart_required": False
    },
    "log_level": {
        "default": "INFO",
        "type": "string",
        "category": "privacy",
        "validation": "enum:DEBUG,INFO,WARNING,ERROR",
        "restart_required": False
    },

    # Advanced (4 settings)
    "database_path": {
        "default": "data/mailmind.db",
        "type": "string",
        "category": "advanced",
        "validation": None,
        "restart_required": True
    },
    "debug_mode": {
        "default": False,
        "type": "bool",
        "category": "advanced",
        "validation": None,
        "restart_required": False
    },
    "auto_backup": {
        "default": True,
        "type": "bool",
        "category": "advanced",
        "validation": None,
        "restart_required": False
    },
    "backup_frequency_hours": {
        "default": 24,
        "type": "int",
        "category": "advanced",
        "validation": "range:1-168",
        "restart_required": False
    }
}
```

### Project Structure Notes

**New Files to Create:**
```
src/mailmind/core/
├── settings_manager.py          # SettingsManager class (400 lines)
└── settings_schema.py            # SETTINGS_SCHEMA definition (150 lines)

src/mailmind/config/
└── default-settings.yaml         # Default YAML template (100 lines)

tests/unit/
└── test_settings_manager.py      # SettingsManager unit tests (400 lines)

tests/integration/
└── test_settings_integration.py  # Integration tests (300 lines)

examples/
├── settings_demo.py              # Settings operations demo (250 lines)
└── settings_integration_demo.py  # Component integration demo (200 lines)
```

**Files to Update:**
- `src/mailmind/ui/dialogs/settings_dialog.py` - Integrate SettingsManager
- `src/mailmind/ui/theme_manager.py` - Subscribe to "theme" setting changes
- `src/mailmind/core/ollama_manager.py` - Subscribe to "model" and "temperature" settings (if needed)

**Dependencies:**
- No new dependencies required (uses existing: PyYAML, DatabaseManager)

### Architecture Patterns

**Singleton Pattern:**
```python
class SettingsManager:
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
```

**Observer Pattern:**
```python
class SettingsManager:
    def __init__(self):
        self._observers = {}  # {setting_key: [callbacks]}

    def subscribe(self, setting_key: str, callback: Callable):
        """Subscribe to setting changes."""
        if setting_key not in self._observers:
            self._observers[setting_key] = []
        self._observers[setting_key].append(callback)

    def _notify_observers(self, setting_key: str, new_value):
        """Notify observers of setting change."""
        if setting_key in self._observers:
            for callback in self._observers[setting_key]:
                callback(new_value)
```

**Usage Example:**
```python
# In ThemeManager __init__
settings_mgr = SettingsManager.get_instance()
settings_mgr.subscribe("theme", self.set_theme)

# When setting changes
settings_mgr.set_setting("theme", "light")  # ThemeManager.set_theme("light") called automatically
```

### Integration Points

**Story 2.2 (DatabaseManager) Integration:**
```python
from mailmind.database import DatabaseManager

class SettingsManager:
    def load_settings(self):
        db = DatabaseManager.get_instance()
        settings = {}
        for key in SETTINGS_SCHEMA:
            pref = db.get_user_preference(key)
            if pref:
                settings[key] = self._parse_value(pref['value'], pref['value_type'])
            else:
                # Use default
                settings[key] = SETTINGS_SCHEMA[key]['default']
        return settings

    def save_settings(self, settings: dict):
        db = DatabaseManager.get_instance()
        for key, value in settings.items():
            db.set_user_preference(
                key=key,
                value=str(value),
                value_type=SETTINGS_SCHEMA[key]['type'],
                category=SETTINGS_SCHEMA[key]['category']
            )
```

**Story 2.3 (SettingsDialog) Integration:**
```python
# In SettingsDialog __init__
from mailmind.core.settings_manager import SettingsManager

class SettingsDialog:
    def __init__(self, master, **kwargs):
        settings_mgr = SettingsManager.get_instance()
        self.settings = settings_mgr.load_settings()
        # ... create UI

    def _on_save_clicked(self):
        settings_mgr = SettingsManager.get_instance()
        new_settings = self._get_current_settings()

        # Validate
        errors = settings_mgr.validate_settings(new_settings)
        if errors:
            # Show error dialog
            return

        # Save
        settings_mgr.save_settings(new_settings)
        self.destroy()
```

**ThemeManager Integration (Example Observer):**
```python
# In ThemeManager __init__
class ThemeManager:
    def __init__(self):
        settings_mgr = SettingsManager.get_instance()

        # Subscribe to theme changes
        settings_mgr.subscribe("theme", self._on_theme_changed)

        # Load initial theme
        theme = settings_mgr.get_setting("theme")
        self.set_theme(theme)

    def _on_theme_changed(self, new_theme: str):
        """Called when theme setting changes."""
        self.set_theme(new_theme)
```

### YAML Configuration File Format

**Example `config/user-settings.yaml`:**
```yaml
# MailMind User Settings
# Generated: 2025-10-14
# Last Modified: 2025-10-14

# General Settings
general:
  # UI theme: 'dark' or 'light'
  theme: dark

  # Startup behavior: 'normal', 'minimized', or 'tray'
  startup_behavior: normal

  # Show desktop notifications for email events
  show_notifications: true

  # Minimize application to system tray
  minimize_to_tray: false

# AI Model Settings
ai_model:
  # AI model: 'llama3:8b', 'llama3:13b', 'mistral:7b', 'phi3:mini'
  # NOTE: Changing this requires application restart
  model: llama3:8b

  # Temperature (creativity): 0.0 (deterministic) to 1.0 (creative)
  temperature: 0.7

  # Default response length: 'Brief', 'Standard', 'Detailed'
  response_length_default: Standard

  # Default response tone: 'Professional', 'Friendly', 'Formal', 'Casual'
  response_tone_default: Professional

# Performance Settings
performance:
  # Batch processing size: 1-20 emails
  batch_size: 5

  # Cache size limit in MB: 100-5000
  cache_size_mb: 500

  # Use GPU acceleration if available
  # NOTE: Changing this requires application restart
  use_gpu: false

  # Maximum concurrent analyses: 1-5
  max_concurrent: 3

# Privacy Settings
privacy:
  # Send anonymous usage statistics (default: off)
  enable_telemetry: false

  # Send crash reports to help improve MailMind
  enable_crash_reports: true

  # Logging level: 'DEBUG', 'INFO', 'WARNING', 'ERROR'
  log_level: INFO

# Advanced Settings
advanced:
  # Database file location
  # NOTE: Changing this requires application restart
  database_path: data/mailmind.db

  # Enable debug mode (verbose logging)
  debug_mode: false

  # Enable automatic database backups
  auto_backup: true

  # Backup frequency in hours: 1-168 (1 week)
  backup_frequency_hours: 24
```

### Validation Logic

**Validation Functions:**
```python
def validate_setting(key: str, value: any) -> Optional[str]:
    """Validate setting value. Returns error message or None."""
    schema = SETTINGS_SCHEMA[key]

    # Type check
    if schema['type'] == 'int' and not isinstance(value, int):
        return f"{key} must be an integer"
    if schema['type'] == 'float' and not isinstance(value, (int, float)):
        return f"{key} must be a number"
    if schema['type'] == 'bool' and not isinstance(value, bool):
        return f"{key} must be true or false"

    # Validation rules
    validation = schema.get('validation')
    if validation:
        if validation.startswith('enum:'):
            allowed = validation.split(':')[1].split(',')
            if value not in allowed:
                return f"{key} must be one of: {', '.join(allowed)}"

        elif validation.startswith('range:'):
            range_str = validation.split(':')[1]
            min_val, max_val = map(float, range_str.split('-'))
            if not (min_val <= value <= max_val):
                return f"{key} must be between {min_val} and {max_val}"

    return None  # Valid
```

### Technical Constraints

**Thread Safety:**
- Use `threading.Lock()` for singleton initialization
- Use locks when modifying settings to prevent race conditions
- DatabaseManager already provides thread-safe operations

**Performance:**
- Cache loaded settings in memory (don't query database for every get_setting call)
- Only write to database when settings actually change
- Batch database updates when saving multiple settings

**Restart-Required Settings:**
- Model selection (requires model reload)
- Startup behavior (takes effect on next launch)
- Database path (requires database reconnection)
- GPU toggle (requires model reload with GPU settings)

**Settings Migration:**
- Future versions may add new settings
- Load defaults for missing settings
- Database migration should preserve existing user preferences

### Testing Strategy

**Unit Tests (40+ tests):**
- SettingsManager initialization and singleton pattern
- Load settings from database and YAML
- Save settings to database and YAML
- Get/set individual settings
- Validation for all 19 settings (valid and invalid values)
- Observer pattern (subscribe, unsubscribe, notifications)
- Reset to defaults
- Export/import YAML

**Integration Tests (20+ tests):**
- Integration with DatabaseManager (read/write user_preferences)
- Integration with SettingsDialog (load, save, reset)
- Observer notifications to ThemeManager
- YAML file creation and parsing
- Settings changes applied immediately vs requiring restart
- Concurrent access from multiple threads

**Manual Testing Checklist:**
- [ ] Open Settings Dialog, verify all 19 settings load correctly
- [ ] Change each setting and save, verify persisted in database
- [ ] Change theme setting, verify immediate application
- [ ] Change model setting, verify restart warning shown
- [ ] Reset to defaults, verify all settings restored
- [ ] Export settings to YAML, verify file created
- [ ] Edit YAML manually, restart app, verify changes loaded
- [ ] Import settings from YAML, verify conflicts handled
- [ ] Subscribe ThemeManager to theme changes, verify callback triggered
- [ ] Test validation: enter invalid values, verify error messages

---

## References

### Primary Sources
- **Epic Breakdown**: `docs/epic-stories.md` - Story 2.4 specification (lines 382-424)
- **Story 2.2**: `docs/stories/story-2.2.md` - user_preferences table schema
- **Story 2.3 SettingsDialog**: `src/mailmind/ui/dialogs/settings_dialog.py` - UI component with 19 settings

### Technical Documentation
- **Python threading**: https://docs.python.org/3/library/threading.html
- **PyYAML**: https://pyyaml.org/wiki/PyYAMLDocumentation
- **Observer Pattern**: https://refactoring.guru/design-patterns/observer

### Integration Dependencies
- **Story 2.2 (DatabaseManager)**: Provides user_preferences table for settings storage
- **Story 2.3 (SettingsDialog)**: Provides UI component - this story adds backend integration
- **Story 1.1 (OllamaManager)**: Consumes model and temperature settings
- **Story 1.6 (PerformanceTracker)**: Consumes performance settings

---

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

*To be filled by DEV agent during implementation*

### Completion Notes List

*To be filled by DEV agent during implementation*

### File List

*To be filled by DEV agent during implementation*

---

## Change Log

### 2025-10-14 - SM Agent (create-story workflow)
- **Action**: Created Story 2.4 draft from epic-stories.md, Story 2.2, and Story 2.3
- **Details**:
  - Story extracted from Epic 2 specifications
  - 9 comprehensive acceptance criteria defined (AC1-AC9)
  - 9 implementation tasks with 40+ subtasks
  - Complete settings schema with all 19 settings and validation rules
  - Integration with DatabaseManager's user_preferences table
  - Integration with existing SettingsDialog UI component
  - Observer pattern for settings change notifications
  - YAML configuration file support for power users
  - Export/import functionality for settings backup
  - Validation logic for all setting types and ranges
  - Immediate vs restart-required settings categorization
  - Testing strategy defined (40+ unit tests, 20+ integration tests)
- **Status**: Draft (awaiting review via story-ready workflow)
- **Next**: User should review story and run `story-ready` to approve for development

---

*This story completes the settings management layer for MailMind, connecting the UI components from Story 2.3 with the persistent storage from Story 2.2, and enabling full application customization.*
