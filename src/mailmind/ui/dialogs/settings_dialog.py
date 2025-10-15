"""
Settings Dialog

Implements Story 2.3 AC2, AC7: Settings dialog with tabbed interface
- General tab (theme, startup, notifications)
- AI Model tab (model selection, temperature, defaults)
- Performance tab (batch size, cache, hardware)
- Privacy tab (telemetry, logging)
- Advanced tab (database, debug mode)
"""

import logging
import customtkinter as ctk
from typing import Optional, Dict, Callable

logger = logging.getLogger(__name__)


class SettingsDialog(ctk.CTkToplevel):
    """
    Settings dialog with tabbed interface.

    Features:
    - 5 tabs (General, AI Model, Performance, Privacy, Advanced)
    - Database persistence integration
    - Apply settings immediately where possible
    - Reset to defaults button
    - Validation for inputs
    """

    def __init__(
        self,
        master,
        current_settings: Optional[Dict] = None,
        on_save: Optional[Callable[[Dict], None]] = None,
        on_rerun_wizard: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        """
        Initialize SettingsDialog.

        Args:
            master: Parent window
            current_settings: Current settings dict
            on_save: Callback when settings are saved (receives settings dict)
            on_rerun_wizard: Callback to re-run onboarding wizard
        """
        super().__init__(master, **kwargs)

        self.on_save_callback = on_save
        self.on_rerun_wizard_callback = on_rerun_wizard
        self.settings = current_settings or self._get_default_settings()
        self.original_settings = self.settings.copy()

        # Configure window
        self.title("MailMind Settings")
        self.geometry("700x550")
        self.resizable(False, False)

        # Make modal
        self.transient(master)
        self.grab_set()

        # Create UI
        self._create_widgets()

        logger.debug("SettingsDialog initialized")

    def _get_default_settings(self) -> Dict:
        """Get default settings."""
        return {
            # General
            "theme": "dark",
            "startup_behavior": "normal",
            "show_notifications": True,
            "minimize_to_tray": False,

            # AI Model
            "model": "llama3:8b",
            "temperature": 0.7,
            "response_length_default": "Standard",
            "response_tone_default": "Professional",

            # Performance
            "batch_size": 5,
            "cache_size_mb": 500,
            "use_gpu": False,
            "max_concurrent": 3,

            # Privacy
            "enable_telemetry": False,
            "enable_crash_reports": True,
            "log_level": "INFO",

            # Advanced
            "database_path": "data/mailmind.db",
            "debug_mode": False,
            "auto_backup": True,
            "backup_frequency_hours": 24
        }

    def _create_widgets(self):
        """Create dialog widgets."""
        # Header
        header = ctk.CTkLabel(
            self,
            text="Settings",
            font=("Segoe UI", 18, "bold")
        )
        header.pack(pady=15)

        # Tabview
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)

        # Create tabs
        self.tab_general = self.tabview.add("General")
        self.tab_ai_model = self.tabview.add("AI Model")
        self.tab_performance = self.tabview.add("Performance")
        self.tab_privacy = self.tabview.add("Privacy")
        self.tab_advanced = self.tabview.add("Advanced")

        # Populate tabs
        self._create_general_tab()
        self._create_ai_model_tab()
        self._create_performance_tab()
        self._create_privacy_tab()
        self._create_advanced_tab()

        # Action buttons
        self._create_action_buttons()

    def _create_general_tab(self):
        """Create General tab."""
        # Theme
        theme_frame = ctk.CTkFrame(self.tab_general)
        theme_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            theme_frame,
            text="Theme:",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=10, pady=5)

        self.theme_var = ctk.StringVar(value=self.settings["theme"])
        theme_options = ctk.CTkFrame(theme_frame, fg_color="transparent")
        theme_options.pack(fill="x", padx=20, pady=5)

        ctk.CTkRadioButton(
            theme_options,
            text="Dark",
            variable=self.theme_var,
            value="dark"
        ).pack(anchor="w")

        ctk.CTkRadioButton(
            theme_options,
            text="Light",
            variable=self.theme_var,
            value="light"
        ).pack(anchor="w")

        # Startup behavior
        startup_frame = ctk.CTkFrame(self.tab_general)
        startup_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            startup_frame,
            text="Startup Behavior:",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=10, pady=5)

        self.startup_var = ctk.StringVar(value=self.settings["startup_behavior"])
        ctk.CTkOptionMenu(
            startup_frame,
            variable=self.startup_var,
            values=["normal", "minimized", "tray"],
            width=200
        ).pack(anchor="w", padx=20, pady=5)

        # Notifications
        notif_frame = ctk.CTkFrame(self.tab_general)
        notif_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            notif_frame,
            text="Notifications:",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=10, pady=5)

        self.show_notifications_var = ctk.BooleanVar(value=self.settings["show_notifications"])
        ctk.CTkCheckBox(
            notif_frame,
            text="Show desktop notifications",
            variable=self.show_notifications_var
        ).pack(anchor="w", padx=20, pady=2)

        self.minimize_to_tray_var = ctk.BooleanVar(value=self.settings["minimize_to_tray"])
        ctk.CTkCheckBox(
            notif_frame,
            text="Minimize to system tray",
            variable=self.minimize_to_tray_var
        ).pack(anchor="w", padx=20, pady=2)

        # Setup Wizard
        wizard_frame = ctk.CTkFrame(self.tab_general)
        wizard_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            wizard_frame,
            text="Setup Wizard:",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=10, pady=5)

        rerun_btn = ctk.CTkButton(
            wizard_frame,
            text="Re-run Setup Wizard",
            command=self._on_rerun_wizard_clicked,
            width=180,
            fg_color="transparent",
            border_width=1
        )
        rerun_btn.pack(anchor="w", padx=20, pady=5)

        wizard_desc = ctk.CTkLabel(
            wizard_frame,
            text="Run the setup wizard again to reconfigure hardware detection, Outlook connection, and initial setup.",
            font=("Segoe UI", 9),
            wraplength=600,
            text_color="gray"
        )
        wizard_desc.pack(anchor="w", padx=20, pady=2)

    def _create_ai_model_tab(self):
        """Create AI Model tab."""
        # Model selection
        model_frame = ctk.CTkFrame(self.tab_ai_model)
        model_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            model_frame,
            text="AI Model:",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=10, pady=5)

        self.model_var = ctk.StringVar(value=self.settings["model"])
        ctk.CTkOptionMenu(
            model_frame,
            variable=self.model_var,
            values=["llama3:8b", "llama3:13b", "mistral:7b", "phi3:mini"],
            width=250
        ).pack(anchor="w", padx=20, pady=5)

        # Temperature
        temp_frame = ctk.CTkFrame(self.tab_ai_model)
        temp_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            temp_frame,
            text="Temperature (creativity):",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=10, pady=5)

        self.temperature_var = ctk.DoubleVar(value=self.settings["temperature"])
        temp_slider = ctk.CTkSlider(
            temp_frame,
            from_=0.0,
            to=1.0,
            variable=self.temperature_var,
            width=300
        )
        temp_slider.pack(anchor="w", padx=20, pady=5)

        self.temp_label = ctk.CTkLabel(
            temp_frame,
            text=f"{self.settings['temperature']:.2f}",
            font=("Segoe UI", 10)
        )
        self.temp_label.pack(anchor="w", padx=20)

        temp_slider.configure(command=lambda v: self.temp_label.configure(text=f"{v:.2f}"))

        # Response defaults
        defaults_frame = ctk.CTkFrame(self.tab_ai_model)
        defaults_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            defaults_frame,
            text="Response Defaults:",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=10, pady=5)

        # Length default
        ctk.CTkLabel(
            defaults_frame,
            text="Default Length:",
            font=("Segoe UI", 10)
        ).pack(anchor="w", padx=20, pady=2)

        self.response_length_var = ctk.StringVar(value=self.settings["response_length_default"])
        ctk.CTkOptionMenu(
            defaults_frame,
            variable=self.response_length_var,
            values=["Brief", "Standard", "Detailed"],
            width=150
        ).pack(anchor="w", padx=20, pady=2)

        # Tone default
        ctk.CTkLabel(
            defaults_frame,
            text="Default Tone:",
            font=("Segoe UI", 10)
        ).pack(anchor="w", padx=20, pady=2)

        self.response_tone_var = ctk.StringVar(value=self.settings["response_tone_default"])
        ctk.CTkOptionMenu(
            defaults_frame,
            variable=self.response_tone_var,
            values=["Professional", "Friendly", "Formal", "Casual"],
            width=150
        ).pack(anchor="w", padx=20, pady=2)

    def _create_performance_tab(self):
        """Create Performance tab."""
        # Batch size
        batch_frame = ctk.CTkFrame(self.tab_performance)
        batch_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            batch_frame,
            text="Batch Processing Size:",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=10, pady=5)

        self.batch_size_var = ctk.IntVar(value=self.settings["batch_size"])
        batch_slider = ctk.CTkSlider(
            batch_frame,
            from_=1,
            to=20,
            number_of_steps=19,
            variable=self.batch_size_var,
            width=300
        )
        batch_slider.pack(anchor="w", padx=20, pady=5)

        self.batch_label = ctk.CTkLabel(
            batch_frame,
            text=f"{self.settings['batch_size']} emails at once",
            font=("Segoe UI", 10)
        )
        self.batch_label.pack(anchor="w", padx=20)

        batch_slider.configure(command=lambda v: self.batch_label.configure(text=f"{int(v)} emails at once"))

        # Cache size
        cache_frame = ctk.CTkFrame(self.tab_performance)
        cache_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            cache_frame,
            text="Cache Size (MB):",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=10, pady=5)

        self.cache_size_var = ctk.IntVar(value=self.settings["cache_size_mb"])
        ctk.CTkEntry(
            cache_frame,
            textvariable=self.cache_size_var,
            width=100
        ).pack(anchor="w", padx=20, pady=5)

        # Hardware
        hardware_frame = ctk.CTkFrame(self.tab_performance)
        hardware_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            hardware_frame,
            text="Hardware:",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=10, pady=5)

        self.use_gpu_var = ctk.BooleanVar(value=self.settings["use_gpu"])
        ctk.CTkCheckBox(
            hardware_frame,
            text="Use GPU acceleration (if available)",
            variable=self.use_gpu_var
        ).pack(anchor="w", padx=20, pady=2)

        # Max concurrent
        ctk.CTkLabel(
            hardware_frame,
            text="Max Concurrent Analyses:",
            font=("Segoe UI", 10)
        ).pack(anchor="w", padx=20, pady=5)

        self.max_concurrent_var = ctk.IntVar(value=self.settings["max_concurrent"])
        ctk.CTkOptionMenu(
            hardware_frame,
            variable=self.max_concurrent_var,
            values=["1", "2", "3", "4", "5"],
            width=100
        ).pack(anchor="w", padx=20, pady=2)

    def _create_privacy_tab(self):
        """Create Privacy tab."""
        # Telemetry
        telemetry_frame = ctk.CTkFrame(self.tab_privacy)
        telemetry_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            telemetry_frame,
            text="Data Collection:",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=10, pady=5)

        self.enable_telemetry_var = ctk.BooleanVar(value=self.settings["enable_telemetry"])
        ctk.CTkCheckBox(
            telemetry_frame,
            text="Send anonymous usage statistics",
            variable=self.enable_telemetry_var
        ).pack(anchor="w", padx=20, pady=2)

        self.enable_crash_reports_var = ctk.BooleanVar(value=self.settings["enable_crash_reports"])
        ctk.CTkCheckBox(
            telemetry_frame,
            text="Send crash reports",
            variable=self.enable_crash_reports_var
        ).pack(anchor="w", padx=20, pady=2)

        # Logging
        logging_frame = ctk.CTkFrame(self.tab_privacy)
        logging_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            logging_frame,
            text="Logging Level:",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=10, pady=5)

        self.log_level_var = ctk.StringVar(value=self.settings["log_level"])
        ctk.CTkOptionMenu(
            logging_frame,
            variable=self.log_level_var,
            values=["DEBUG", "INFO", "WARNING", "ERROR"],
            width=150
        ).pack(anchor="w", padx=20, pady=5)

        # Privacy notice
        notice = ctk.CTkTextbox(self.tab_privacy, height=100, wrap="word")
        notice.pack(fill="x", padx=10, pady=10)
        notice.insert("1.0", "Privacy Notice:\n\nMailMind processes all emails locally on your machine. No email content is ever sent to external servers. Telemetry data (if enabled) includes only anonymous usage metrics and does not include email content or personal information.")
        notice.configure(state="disabled")

    def _create_advanced_tab(self):
        """Create Advanced tab."""
        # Database path
        db_frame = ctk.CTkFrame(self.tab_advanced)
        db_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            db_frame,
            text="Database Location:",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=10, pady=5)

        self.database_path_var = ctk.StringVar(value=self.settings["database_path"])
        ctk.CTkEntry(
            db_frame,
            textvariable=self.database_path_var,
            width=400
        ).pack(anchor="w", padx=20, pady=5)

        # Debug mode
        debug_frame = ctk.CTkFrame(self.tab_advanced)
        debug_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            debug_frame,
            text="Developer Options:",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=10, pady=5)

        self.debug_mode_var = ctk.BooleanVar(value=self.settings["debug_mode"])
        ctk.CTkCheckBox(
            debug_frame,
            text="Enable debug mode",
            variable=self.debug_mode_var
        ).pack(anchor="w", padx=20, pady=2)

        # Auto backup
        backup_frame = ctk.CTkFrame(self.tab_advanced)
        backup_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            backup_frame,
            text="Backup Settings:",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=10, pady=5)

        self.auto_backup_var = ctk.BooleanVar(value=self.settings["auto_backup"])
        ctk.CTkCheckBox(
            backup_frame,
            text="Enable automatic database backup",
            variable=self.auto_backup_var
        ).pack(anchor="w", padx=20, pady=2)

        ctk.CTkLabel(
            backup_frame,
            text="Backup frequency (hours):",
            font=("Segoe UI", 10)
        ).pack(anchor="w", padx=20, pady=5)

        self.backup_frequency_var = ctk.IntVar(value=self.settings["backup_frequency_hours"])
        ctk.CTkEntry(
            backup_frame,
            textvariable=self.backup_frequency_var,
            width=100
        ).pack(anchor="w", padx=20, pady=2)

    def _create_action_buttons(self):
        """Create action buttons."""
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=20, pady=10)

        # Reset to defaults
        reset_btn = ctk.CTkButton(
            button_frame,
            text="Reset to Defaults",
            command=self._on_reset_clicked,
            width=140,
            fg_color="transparent",
            border_width=1
        )
        reset_btn.pack(side="left", padx=5)

        # Cancel
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self._on_cancel_clicked,
            width=100,
            fg_color="transparent",
            border_width=1
        )
        cancel_btn.pack(side="right", padx=5)

        # Save
        save_btn = ctk.CTkButton(
            button_frame,
            text="Save",
            command=self._on_save_clicked,
            width=100
        )
        save_btn.pack(side="right", padx=5)

    def _get_current_settings(self) -> Dict:
        """Get current settings from UI."""
        return {
            # General
            "theme": self.theme_var.get(),
            "startup_behavior": self.startup_var.get(),
            "show_notifications": self.show_notifications_var.get(),
            "minimize_to_tray": self.minimize_to_tray_var.get(),

            # AI Model
            "model": self.model_var.get(),
            "temperature": self.temperature_var.get(),
            "response_length_default": self.response_length_var.get(),
            "response_tone_default": self.response_tone_var.get(),

            # Performance
            "batch_size": self.batch_size_var.get(),
            "cache_size_mb": self.cache_size_var.get(),
            "use_gpu": self.use_gpu_var.get(),
            "max_concurrent": self.max_concurrent_var.get(),

            # Privacy
            "enable_telemetry": self.enable_telemetry_var.get(),
            "enable_crash_reports": self.enable_crash_reports_var.get(),
            "log_level": self.log_level_var.get(),

            # Advanced
            "database_path": self.database_path_var.get(),
            "debug_mode": self.debug_mode_var.get(),
            "auto_backup": self.auto_backup_var.get(),
            "backup_frequency_hours": self.backup_frequency_var.get()
        }

    def _on_save_clicked(self):
        """Handle Save button click."""
        self.settings = self._get_current_settings()

        logger.debug("Settings saved")

        # Call callback
        if self.on_save_callback:
            self.on_save_callback(self.settings)

        self.destroy()

    def _on_cancel_clicked(self):
        """Handle Cancel button click."""
        logger.debug("Settings cancelled")
        self.destroy()

    def _on_reset_clicked(self):
        """Handle Reset to Defaults button click."""
        # Confirm reset
        confirm = ctk.CTkInputDialog(
            text="Reset all settings to defaults?\nThis cannot be undone.",
            title="Confirm Reset"
        )

        if confirm.get_input():
            self.settings = self._get_default_settings()
            self.destroy()

            # Reopen with defaults
            dialog = SettingsDialog(
                self.master,
                current_settings=self.settings,
                on_save=self.on_save_callback
            )

            logger.debug("Settings reset to defaults")

    def _on_rerun_wizard_clicked(self):
        """Handle Re-run Setup Wizard button click."""
        logger.debug("Re-run setup wizard requested")

        # Close settings dialog
        self.destroy()

        # Call callback to launch wizard
        if self.on_rerun_wizard_callback:
            self.on_rerun_wizard_callback()
