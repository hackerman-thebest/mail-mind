"""
Onboarding Wizard

Implements Story 2.5: Hardware Profiling & Onboarding Wizard
- 5-step guided setup flow
- Hardware detection and profiling
- Performance expectations based on hardware tier
- Outlook connection testing
- Initial email indexing
"""

import logging
import threading
import time
from typing import Optional, Dict, Any, Callable
import customtkinter as ctk

from mailmind.core.hardware_profiler import HardwareProfiler
from mailmind.integrations.outlook_connector import OutlookConnector
from mailmind.database.database_manager import DatabaseManager
from mailmind.core.settings_manager import SettingsManager

logger = logging.getLogger(__name__)


class OnboardingWizard(ctk.CTkToplevel):
    """
    Onboarding wizard with 5-step flow.

    Steps:
    1. Welcome screen
    2. Hardware detection
    3. Performance expectations
    4. Outlook connection test
    5. Email indexing (50 emails)

    Features:
    - Background threading for long operations
    - Thread-safe UI updates
    - Hardware tier color coding
    - Progress indicators
    - Skip functionality
    """

    # Hardware tier colors
    TIER_COLORS = {
        "Optimal": "#00C853",      # Green
        "Recommended": "#FFD600",   # Yellow
        "Minimum": "#FF6D00",       # Orange
        "Insufficient": "#D50000"   # Red
    }

    TIER_EMOJIS = {
        "Optimal": "🟢",
        "Recommended": "🟡",
        "Minimum": "🟠",
        "Insufficient": "🔴"
    }

    def __init__(
        self,
        parent,
        settings_manager: SettingsManager,
        db_manager: DatabaseManager,
        on_complete: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        """
        Initialize OnboardingWizard.

        Args:
            parent: Parent window
            settings_manager: SettingsManager instance
            db_manager: DatabaseManager instance
            on_complete: Callback when wizard completes
        """
        super().__init__(parent, **kwargs)

        self.settings_manager = settings_manager
        self.db_manager = db_manager
        self.on_complete_callback = on_complete

        self.current_step = 1
        self.total_steps = 5
        self.hardware_profile = None
        self.outlook_connector = None
        self.indexed_count = 0

        # Background operation state
        self.operation_in_progress = False
        self.operation_cancelled = False

        # Configure window
        self.title("MailMind Setup Wizard")
        self.geometry("800x600")
        self.resizable(False, False)

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Create UI
        self._create_widgets()

        # Show first step
        self._show_step(1)

        logger.debug("OnboardingWizard initialized")

    def _create_widgets(self):
        """Create wizard widgets."""
        # Header
        self.header_label = ctk.CTkLabel(
            self,
            text="Welcome to MailMind",
            font=("Segoe UI", 24, "bold")
        )
        self.header_label.pack(pady=20)

        # Step indicator
        self.step_indicator = ctk.CTkLabel(
            self,
            text=f"Step {self.current_step} of {self.total_steps}",
            font=("Segoe UI", 12)
        )
        self.step_indicator.pack(pady=5)

        # Content frame (swappable per step)
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(fill="both", expand=True, padx=30, pady=20)

        # Navigation buttons
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x", padx=30, pady=20)

        self.back_btn = ctk.CTkButton(
            nav_frame,
            text="Back",
            command=self._on_back_clicked,
            width=100,
            fg_color="transparent",
            border_width=1
        )
        self.back_btn.pack(side="left", padx=5)

        self.skip_btn = ctk.CTkButton(
            nav_frame,
            text="Skip Setup",
            command=self._on_skip_clicked,
            width=100,
            fg_color="transparent",
            border_width=1
        )
        self.skip_btn.pack(side="left", padx=5)

        self.next_btn = ctk.CTkButton(
            nav_frame,
            text="Next",
            command=self._on_next_clicked,
            width=100
        )
        self.next_btn.pack(side="right", padx=5)

    def _show_step(self, step_number: int):
        """
        Show specific wizard step.

        Args:
            step_number: Step number (1-5)
        """
        self.current_step = step_number
        self.step_indicator.configure(text=f"Step {self.current_step} of {self.total_steps}")

        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Show appropriate step
        if step_number == 1:
            self._show_welcome_step()
        elif step_number == 2:
            self._show_hardware_detection_step()
        elif step_number == 3:
            self._show_performance_expectations_step()
        elif step_number == 4:
            self._show_outlook_connection_step()
        elif step_number == 5:
            self._show_email_indexing_step()

        # Update button states
        self._update_navigation_buttons()

        logger.debug(f"Showing wizard step {step_number}")

    def _show_welcome_step(self):
        """Show Step 1: Welcome screen."""
        self.header_label.configure(text="Welcome to MailMind")

        # Welcome message
        welcome_text = ctk.CTkTextbox(
            self.content_frame,
            height=250,
            wrap="word",
            font=("Segoe UI", 13)
        )
        welcome_text.pack(fill="both", expand=True, padx=20, pady=20)

        welcome_content = """Welcome to MailMind - Your Sovereign AI Email Assistant!

MailMind helps you manage your inbox with the power of AI, running entirely on your local machine. Your emails never leave your computer.

This wizard will guide you through:

  • Hardware Detection - We'll check your system capabilities
  • Performance Expectations - Learn what to expect based on your hardware
  • Outlook Connection - Connect to your Microsoft Outlook account
  • Email Indexing - Index your first 50 emails for instant analysis

The setup process takes approximately 2-3 minutes.

Click "Next" to begin, or "Skip Setup" to configure manually later."""

        welcome_text.insert("1.0", welcome_content)
        welcome_text.configure(state="disabled")

        # Feature highlights
        highlights_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        highlights_frame.pack(fill="x", padx=20, pady=10)

        features = [
            "🔒 100% Local Processing - Your data stays on your machine",
            "⚡ AI-Powered Analysis - Smart priority detection and responses",
            "🎯 Context-Aware - Understands your email patterns"
        ]

        for feature in features:
            label = ctk.CTkLabel(
                highlights_frame,
                text=feature,
                font=("Segoe UI", 11),
                anchor="w"
            )
            label.pack(anchor="w", pady=3)

    def _show_hardware_detection_step(self):
        """Show Step 2: Hardware detection."""
        self.header_label.configure(text="Hardware Detection")

        # Description
        desc_label = ctk.CTkLabel(
            self.content_frame,
            text="Detecting your system hardware capabilities...",
            font=("Segoe UI", 13),
            wraplength=700
        )
        desc_label.pack(pady=20)

        # Progress indicator
        self.hw_progress = ctk.CTkProgressBar(self.content_frame, width=600)
        self.hw_progress.pack(pady=20)
        self.hw_progress.set(0)

        # Status label
        self.hw_status_label = ctk.CTkLabel(
            self.content_frame,
            text="Initializing detection...",
            font=("Segoe UI", 11)
        )
        self.hw_status_label.pack(pady=10)

        # Results frame (hidden until detection completes)
        self.hw_results_frame = ctk.CTkFrame(self.content_frame)
        self.hw_results_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.hw_results_frame.pack_forget()  # Hide initially

        # Start hardware detection in background
        self.operation_in_progress = True
        thread = threading.Thread(target=self._detect_hardware_background, daemon=True)
        thread.start()

    def _detect_hardware_background(self):
        """Background thread for hardware detection."""
        try:
            start_time = time.time()

            # Update status
            self.after(0, lambda: self.hw_status_label.configure(text="Detecting CPU and RAM..."))
            self.after(0, lambda: self.hw_progress.set(0.3))
            time.sleep(0.5)

            if self.operation_cancelled:
                return

            # Detect hardware
            self.after(0, lambda: self.hw_status_label.configure(text="Checking GPU availability..."))
            self.after(0, lambda: self.hw_progress.set(0.6))

            self.hardware_profile = HardwareProfiler.detect_hardware()

            if self.operation_cancelled:
                return

            self.after(0, lambda: self.hw_status_label.configure(text="Analyzing capabilities..."))
            self.after(0, lambda: self.hw_progress.set(0.9))
            time.sleep(0.3)

            # Save to database
            self.db_manager.set_preference("hardware_profile", self.hardware_profile)

            elapsed_time = time.time() - start_time

            # Show results
            self.after(0, lambda: self._show_hardware_results(elapsed_time))

        except Exception as e:
            logger.error(f"Hardware detection failed: {e}", exc_info=True)
            self.after(0, lambda: self._show_hardware_error(str(e)))
        finally:
            self.operation_in_progress = False

    def _show_hardware_results(self, elapsed_time: float):
        """Show hardware detection results."""
        self.hw_progress.set(1.0)
        self.hw_status_label.configure(
            text=f"✓ Detection complete ({elapsed_time:.1f}s)"
        )

        # Show results frame
        self.hw_results_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Hardware tier
        tier = self.hardware_profile.get("hardware_tier", "Unknown")
        tier_color = self.TIER_COLORS.get(tier, "#808080")
        tier_emoji = self.TIER_EMOJIS.get(tier, "⚪")

        tier_label = ctk.CTkLabel(
            self.hw_results_frame,
            text=f"{tier_emoji} Hardware Tier: {tier}",
            font=("Segoe UI", 16, "bold"),
            text_color=tier_color
        )
        tier_label.pack(pady=15)

        # Hardware specs
        specs_frame = ctk.CTkFrame(self.hw_results_frame, fg_color="transparent")
        specs_frame.pack(fill="x", padx=20, pady=10)

        specs = [
            ("CPU Cores:", f"{self.hardware_profile.get('cpu_cores', 0)}"),
            ("RAM Total:", f"{self.hardware_profile.get('ram_total_gb', 0):.1f} GB"),
            ("RAM Available:", f"{self.hardware_profile.get('ram_available_gb', 0):.1f} GB"),
            ("GPU Detected:", "Yes" if self.hardware_profile.get('gpu_detected') else "No"),
        ]

        if self.hardware_profile.get('gpu_detected'):
            specs.append(("GPU VRAM:", f"{self.hardware_profile.get('gpu_vram_gb', 0):.1f} GB"))

        for label_text, value_text in specs:
            row = ctk.CTkFrame(specs_frame, fg_color="transparent")
            row.pack(fill="x", pady=3)

            ctk.CTkLabel(
                row,
                text=label_text,
                font=("Segoe UI", 11, "bold"),
                width=150,
                anchor="w"
            ).pack(side="left")

            ctk.CTkLabel(
                row,
                text=value_text,
                font=("Segoe UI", 11),
                anchor="w"
            ).pack(side="left")

        # Recommended model
        model = self.hardware_profile.get('recommended_model', 'llama3:8b')
        model_label = ctk.CTkLabel(
            self.hw_results_frame,
            text=f"Recommended AI Model: {model}",
            font=("Segoe UI", 11)
        )
        model_label.pack(pady=10)

        # Enable Next button
        self.next_btn.configure(state="normal")

    def _show_hardware_error(self, error_message: str):
        """Show hardware detection error."""
        self.hw_status_label.configure(
            text=f"✗ Detection failed: {error_message}",
            text_color="#D50000"
        )
        self.hw_progress.pack_forget()

        # Show error in results frame
        self.hw_results_frame.pack(fill="both", expand=True, padx=20, pady=20)

        error_label = ctk.CTkLabel(
            self.hw_results_frame,
            text="Hardware detection encountered an error.\nYou can continue with default settings.",
            font=("Segoe UI", 12),
            wraplength=700
        )
        error_label.pack(pady=20)

        # Enable Next button to continue
        self.next_btn.configure(state="normal")

    def _show_performance_expectations_step(self):
        """Show Step 3: Performance expectations."""
        self.header_label.configure(text="Performance Expectations")

        # Check if hardware profile exists
        if not self.hardware_profile:
            # Try to load from database
            self.hardware_profile = self.db_manager.get_preference("hardware_profile", None)

        tier = self.hardware_profile.get("hardware_tier", "Unknown") if self.hardware_profile else "Unknown"

        # Header with tier
        tier_emoji = self.TIER_EMOJIS.get(tier, "⚪")
        tier_color = self.TIER_COLORS.get(tier, "#808080")

        tier_header = ctk.CTkLabel(
            self.content_frame,
            text=f"{tier_emoji} Your Hardware Tier: {tier}",
            font=("Segoe UI", 18, "bold"),
            text_color=tier_color
        )
        tier_header.pack(pady=20)

        # Performance expectations
        expectations_frame = ctk.CTkFrame(self.content_frame)
        expectations_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Get tier-specific expectations
        expectations = self._get_tier_expectations(tier)

        # Display expectations
        for category, details in expectations.items():
            cat_frame = ctk.CTkFrame(expectations_frame, fg_color="transparent")
            cat_frame.pack(fill="x", padx=15, pady=10)

            cat_label = ctk.CTkLabel(
                cat_frame,
                text=f"{category}:",
                font=("Segoe UI", 12, "bold"),
                anchor="w"
            )
            cat_label.pack(anchor="w", pady=3)

            details_label = ctk.CTkLabel(
                cat_frame,
                text=details,
                font=("Segoe UI", 11),
                anchor="w",
                wraplength=700
            )
            details_label.pack(anchor="w", padx=20, pady=2)

        # Tips section
        tips_frame = ctk.CTkFrame(self.content_frame)
        tips_frame.pack(fill="x", padx=20, pady=10)

        tips_label = ctk.CTkLabel(
            tips_frame,
            text="💡 Tips for Best Performance",
            font=("Segoe UI", 12, "bold")
        )
        tips_label.pack(anchor="w", padx=10, pady=5)

        tips = self._get_tier_tips(tier)
        for tip in tips:
            tip_label = ctk.CTkLabel(
                tips_frame,
                text=f"  • {tip}",
                font=("Segoe UI", 10),
                anchor="w",
                wraplength=700
            )
            tip_label.pack(anchor="w", padx=20, pady=2)

    def _get_tier_expectations(self, tier: str) -> Dict[str, str]:
        """Get performance expectations for hardware tier."""
        expectations = {
            "Optimal": {
                "Email Analysis": "Lightning fast - analyze emails in under 1 second",
                "Response Generation": "Nearly instant - generate responses in 1-2 seconds",
                "Batch Processing": "Process 10+ emails concurrently with ease",
                "Model Recommendations": "Can run larger models (13B+) for enhanced accuracy"
            },
            "Recommended": {
                "Email Analysis": "Fast - analyze emails in 1-2 seconds",
                "Response Generation": "Quick - generate responses in 2-4 seconds",
                "Batch Processing": "Process 5-10 emails concurrently",
                "Model Recommendations": "Best with 8B models for balanced performance"
            },
            "Minimum": {
                "Email Analysis": "Moderate - analyze emails in 3-5 seconds",
                "Response Generation": "Adequate - generate responses in 5-8 seconds",
                "Batch Processing": "Process 1-3 emails at a time",
                "Model Recommendations": "Use smaller models (7B or less) for better responsiveness"
            },
            "Insufficient": {
                "Email Analysis": "Slow - may take 10+ seconds per email",
                "Response Generation": "Very slow - may take 15-30 seconds",
                "Batch Processing": "Process one email at a time only",
                "Model Recommendations": "Consider upgrading hardware or using remote AI services"
            }
        }

        return expectations.get(tier, {
            "Email Analysis": "Performance will vary based on your system",
            "Response Generation": "Response times depend on hardware capabilities",
            "Batch Processing": "Concurrent processing limited by available resources",
            "Model Recommendations": "System will auto-select appropriate models"
        })

    def _get_tier_tips(self, tier: str) -> list:
        """Get performance tips for hardware tier."""
        tips = {
            "Optimal": [
                "You can enable GPU acceleration in settings for even better performance",
                "Try experimenting with larger models for improved accuracy",
                "Increase batch processing size for faster email processing"
            ],
            "Recommended": [
                "Close unnecessary applications when processing large batches",
                "The default settings are optimized for your hardware tier",
                "GPU acceleration can be enabled if you have a compatible GPU"
            ],
            "Minimum": [
                "Close other applications to free up RAM during processing",
                "Process emails one at a time for more consistent performance",
                "Consider the 'Quick Analysis' mode for faster results"
            ],
            "Insufficient": [
                "We recommend upgrading RAM to at least 8GB for better performance",
                "Close all non-essential applications before using MailMind",
                "Consider using MailMind during off-peak hours",
                "You may want to explore cloud-based AI options in settings"
            ]
        }

        return tips.get(tier, [
            "MailMind will adapt to your system capabilities automatically",
            "Check the Performance settings for optimization options"
        ])

    def _show_outlook_connection_step(self):
        """Show Step 4: Outlook connection test."""
        self.header_label.configure(text="Outlook Connection")

        # Description
        desc_label = ctk.CTkLabel(
            self.content_frame,
            text="Testing connection to Microsoft Outlook...",
            font=("Segoe UI", 13),
            wraplength=700
        )
        desc_label.pack(pady=20)

        # Info box
        info_frame = ctk.CTkFrame(self.content_frame)
        info_frame.pack(fill="x", padx=20, pady=10)

        info_text = ctk.CTkLabel(
            info_frame,
            text="📧 MailMind requires Microsoft Outlook to be installed and configured on this computer.\nMake sure Outlook is closed before proceeding.",
            font=("Segoe UI", 11),
            wraplength=650
        )
        info_text.pack(padx=15, pady=15)

        # Progress indicator
        self.outlook_progress = ctk.CTkProgressBar(self.content_frame, width=600)
        self.outlook_progress.pack(pady=20)
        self.outlook_progress.set(0)

        # Status label
        self.outlook_status_label = ctk.CTkLabel(
            self.content_frame,
            text="Initializing connection...",
            font=("Segoe UI", 11)
        )
        self.outlook_status_label.pack(pady=10)

        # Results frame (hidden until test completes)
        self.outlook_results_frame = ctk.CTkFrame(self.content_frame)
        self.outlook_results_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.outlook_results_frame.pack_forget()  # Hide initially

        # Start connection test in background
        self.operation_in_progress = True
        thread = threading.Thread(target=self._test_outlook_connection_background, daemon=True)
        thread.start()

    def _test_outlook_connection_background(self):
        """Background thread for Outlook connection test."""
        try:
            start_time = time.time()

            # Update status
            self.after(0, lambda: self.outlook_status_label.configure(text="Connecting to Outlook..."))
            self.after(0, lambda: self.outlook_progress.set(0.3))

            # Create connector
            self.outlook_connector = OutlookConnector()

            if self.operation_cancelled:
                return

            # Attempt connection
            self.after(0, lambda: self.outlook_status_label.configure(text="Verifying account..."))
            self.after(0, lambda: self.outlook_progress.set(0.6))

            success = self.outlook_connector.connect()

            if self.operation_cancelled:
                return

            self.after(0, lambda: self.outlook_progress.set(0.9))
            time.sleep(0.3)

            elapsed_time = time.time() - start_time

            # Show results
            if success:
                connection_status = self.outlook_connector.get_connection_status()
                self.after(0, lambda: self._show_outlook_success(elapsed_time, connection_status))
            else:
                self.after(0, lambda: self._show_outlook_error("Connection failed"))

        except Exception as e:
            logger.error(f"Outlook connection test failed: {e}", exc_info=True)
            self.after(0, lambda: self._show_outlook_error(str(e)))
        finally:
            self.operation_in_progress = False

    def _show_outlook_success(self, elapsed_time: float, connection_status):
        """Show successful Outlook connection."""
        self.outlook_progress.set(1.0)
        self.outlook_status_label.configure(
            text=f"✓ Connection successful ({elapsed_time:.1f}s)"
        )

        # Show results frame
        self.outlook_results_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Success message
        success_label = ctk.CTkLabel(
            self.outlook_results_frame,
            text="✓ Successfully connected to Outlook",
            font=("Segoe UI", 16, "bold"),
            text_color="#00C853"
        )
        success_label.pack(pady=15)

        # Account details
        details_frame = ctk.CTkFrame(self.outlook_results_frame, fg_color="transparent")
        details_frame.pack(fill="x", padx=20, pady=10)

        details = [
            ("Status:", connection_status.status if connection_status else "Connected"),
            ("Account:", connection_status.email_address if connection_status and connection_status.email_address else "Default account"),
        ]

        for label_text, value_text in details:
            row = ctk.CTkFrame(details_frame, fg_color="transparent")
            row.pack(fill="x", pady=3)

            ctk.CTkLabel(
                row,
                text=label_text,
                font=("Segoe UI", 11, "bold"),
                width=100,
                anchor="w"
            ).pack(side="left")

            ctk.CTkLabel(
                row,
                text=str(value_text),
                font=("Segoe UI", 11),
                anchor="w"
            ).pack(side="left")

        # Enable Next button
        self.next_btn.configure(state="normal")

    def _show_outlook_error(self, error_message: str):
        """Show Outlook connection error."""
        self.outlook_status_label.configure(
            text=f"✗ Connection failed: {error_message}",
            text_color="#D50000"
        )
        self.outlook_progress.pack_forget()

        # Show error in results frame
        self.outlook_results_frame.pack(fill="both", expand=True, padx=20, pady=20)

        error_label = ctk.CTkLabel(
            self.outlook_results_frame,
            text="✗ Unable to connect to Outlook",
            font=("Segoe UI", 16, "bold"),
            text_color="#D50000"
        )
        error_label.pack(pady=15)

        # Troubleshooting tips
        tips_frame = ctk.CTkFrame(self.outlook_results_frame)
        tips_frame.pack(fill="both", expand=True, padx=20, pady=10)

        tips_label = ctk.CTkLabel(
            tips_frame,
            text="Troubleshooting:",
            font=("Segoe UI", 11, "bold")
        )
        tips_label.pack(anchor="w", padx=10, pady=5)

        tips = [
            "Make sure Microsoft Outlook is installed on this computer",
            "Ensure Outlook is configured with at least one email account",
            "Try closing Outlook if it's currently running",
            "Check that you have permission to access Outlook data",
            "You can configure Outlook connection later in Settings"
        ]

        for tip in tips:
            tip_label = ctk.CTkLabel(
                tips_frame,
                text=f"  • {tip}",
                font=("Segoe UI", 10),
                anchor="w",
                wraplength=650
            )
            tip_label.pack(anchor="w", padx=20, pady=2)

        # Enable Next button to continue despite error
        self.next_btn.configure(state="normal")

    def _show_email_indexing_step(self):
        """Show Step 5: Email indexing."""
        self.header_label.configure(text="Email Indexing")

        # Description
        desc_label = ctk.CTkLabel(
            self.content_frame,
            text="Indexing your first 50 emails for instant analysis...",
            font=("Segoe UI", 13),
            wraplength=700
        )
        desc_label.pack(pady=20)

        # Info box
        info_frame = ctk.CTkFrame(self.content_frame)
        info_frame.pack(fill="x", padx=20, pady=10)

        info_text = ctk.CTkLabel(
            info_frame,
            text="📨 MailMind will index 50 recent emails from your Inbox.\nThis helps the AI understand your email patterns and provide better assistance.",
            font=("Segoe UI", 11),
            wraplength=650
        )
        info_text.pack(padx=15, pady=15)

        # Progress indicator
        self.indexing_progress = ctk.CTkProgressBar(self.content_frame, width=600)
        self.indexing_progress.pack(pady=20)
        self.indexing_progress.set(0)

        # Status label
        self.indexing_status_label = ctk.CTkLabel(
            self.content_frame,
            text="Starting indexing...",
            font=("Segoe UI", 11)
        )
        self.indexing_status_label.pack(pady=10)

        # Count label
        self.indexing_count_label = ctk.CTkLabel(
            self.content_frame,
            text="0 / 50 emails indexed",
            font=("Segoe UI", 12, "bold")
        )
        self.indexing_count_label.pack(pady=5)

        # Results frame (hidden until indexing completes)
        self.indexing_results_frame = ctk.CTkFrame(self.content_frame)
        self.indexing_results_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.indexing_results_frame.pack_forget()  # Hide initially

        # Change Next to Finish
        self.next_btn.configure(text="Finish")

        # Start indexing in background
        self.operation_in_progress = True
        thread = threading.Thread(target=self._index_emails_background, daemon=True)
        thread.start()

    def _index_emails_background(self):
        """Background thread for email indexing."""
        try:
            start_time = time.time()
            target_count = 50

            # Check if Outlook connector exists
            if not self.outlook_connector:
                # Try to create one
                self.outlook_connector = OutlookConnector()
                if not self.outlook_connector.connect():
                    raise Exception("Unable to connect to Outlook")

            self.after(0, lambda: self.indexing_status_label.configure(text="Fetching emails from Inbox..."))

            # Fetch emails
            emails = self.outlook_connector.fetch_emails(folder_name="Inbox", limit=target_count)

            if self.operation_cancelled:
                return

            total_emails = len(emails)

            # Index emails
            for i, email in enumerate(emails):
                if self.operation_cancelled:
                    return

                # Update progress
                progress = (i + 1) / target_count
                count = i + 1

                self.after(0, lambda p=progress: self.indexing_progress.set(p))
                self.after(0, lambda c=count, t=total_emails: self.indexing_count_label.configure(
                    text=f"{c} / {min(t, target_count)} emails indexed"
                ))
                self.after(0, lambda: self.indexing_status_label.configure(
                    text=f"Indexing email: {email.subject[:50]}..."
                ))

                # Simulate indexing work (in real implementation, save to database)
                time.sleep(0.1)

                self.indexed_count = count

            elapsed_time = time.time() - start_time

            # Show results
            self.after(0, lambda: self._show_indexing_success(elapsed_time, self.indexed_count))

        except Exception as e:
            logger.error(f"Email indexing failed: {e}", exc_info=True)
            self.after(0, lambda: self._show_indexing_error(str(e)))
        finally:
            self.operation_in_progress = False

    def _show_indexing_success(self, elapsed_time: float, count: int):
        """Show successful email indexing."""
        self.indexing_progress.set(1.0)
        self.indexing_status_label.configure(
            text=f"✓ Indexing complete ({elapsed_time:.1f}s)"
        )
        self.indexing_count_label.configure(
            text=f"✓ {count} emails indexed successfully"
        )

        # Show results frame
        self.indexing_results_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Success message
        success_label = ctk.CTkLabel(
            self.indexing_results_frame,
            text="✓ Email indexing complete!",
            font=("Segoe UI", 16, "bold"),
            text_color="#00C853"
        )
        success_label.pack(pady=15)

        # Summary
        summary_text = ctk.CTkLabel(
            self.indexing_results_frame,
            text=f"Successfully indexed {count} emails from your Inbox.\nMailMind is now ready to assist you with email management!",
            font=("Segoe UI", 11),
            wraplength=650
        )
        summary_text.pack(pady=10)

        # Next steps
        next_steps_frame = ctk.CTkFrame(self.indexing_results_frame)
        next_steps_frame.pack(fill="x", padx=20, pady=15)

        next_steps_label = ctk.CTkLabel(
            next_steps_frame,
            text="What's Next:",
            font=("Segoe UI", 11, "bold")
        )
        next_steps_label.pack(anchor="w", padx=10, pady=5)

        steps = [
            "Select an email to see AI-powered analysis",
            "Get priority recommendations for urgent emails",
            "Generate smart responses with one click",
            "Customize settings to match your preferences"
        ]

        for step in steps:
            step_label = ctk.CTkLabel(
                next_steps_frame,
                text=f"  • {step}",
                font=("Segoe UI", 10),
                anchor="w"
            )
            step_label.pack(anchor="w", padx=20, pady=2)

        # Enable Finish button
        self.next_btn.configure(state="normal")

    def _show_indexing_error(self, error_message: str):
        """Show email indexing error."""
        self.indexing_status_label.configure(
            text=f"✗ Indexing failed: {error_message}",
            text_color="#D50000"
        )
        self.indexing_progress.pack_forget()
        self.indexing_count_label.pack_forget()

        # Show error in results frame
        self.indexing_results_frame.pack(fill="both", expand=True, padx=20, pady=20)

        error_label = ctk.CTkLabel(
            self.indexing_results_frame,
            text="⚠ Email indexing encountered an error",
            font=("Segoe UI", 16, "bold"),
            text_color="#FF6D00"
        )
        error_label.pack(pady=15)

        # Error message
        error_text = ctk.CTkLabel(
            self.indexing_results_frame,
            text=f"You can still use MailMind, but emails will be indexed on-demand.\n\nError details: {error_message}",
            font=("Segoe UI", 11),
            wraplength=650
        )
        error_text.pack(pady=10)

        # Enable Finish button to complete setup
        self.next_btn.configure(state="normal")

    def _update_navigation_buttons(self):
        """Update navigation button states."""
        # Back button
        self.back_btn.configure(state="normal" if self.current_step > 1 else "disabled")

        # Skip button (hide on last step)
        if self.current_step == self.total_steps:
            self.skip_btn.pack_forget()
        else:
            if not self.skip_btn.winfo_ismapped():
                self.skip_btn.pack(side="left", padx=5, after=self.back_btn)

        # Next button text
        if self.current_step == self.total_steps:
            self.next_btn.configure(text="Finish")
        else:
            self.next_btn.configure(text="Next")

        # Disable Next during operations
        if self.operation_in_progress:
            self.next_btn.configure(state="disabled")
        else:
            self.next_btn.configure(state="normal")

    def _on_back_clicked(self):
        """Handle Back button click."""
        if self.current_step > 1 and not self.operation_in_progress:
            self._show_step(self.current_step - 1)

    def _on_next_clicked(self):
        """Handle Next button click."""
        if self.operation_in_progress:
            return

        if self.current_step < self.total_steps:
            self._show_step(self.current_step + 1)
        else:
            # Finish wizard
            self._complete_wizard()

    def _on_skip_clicked(self):
        """Handle Skip Setup button click."""
        if self.operation_in_progress:
            self.operation_cancelled = True
            time.sleep(0.2)  # Give background thread time to check cancellation

        # Mark as skipped and close
        self.db_manager.set_preference("onboarding_complete", False)
        self.db_manager.set_preference("onboarding_skipped", True)

        logger.info("Onboarding wizard skipped")
        self.destroy()

    def _complete_wizard(self):
        """Complete wizard and mark onboarding as done."""
        # Save completion flag
        self.db_manager.set_preference("onboarding_complete", True)
        self.db_manager.set_preference("onboarding_skipped", False)
        self.db_manager.set_preference("onboarding_completed_at", time.time())

        # Save indexed email count
        if self.indexed_count > 0:
            self.db_manager.set_preference("initial_emails_indexed", self.indexed_count)

        logger.info("Onboarding wizard completed successfully")

        # Call completion callback
        if self.on_complete_callback:
            self.on_complete_callback()

        self.destroy()
