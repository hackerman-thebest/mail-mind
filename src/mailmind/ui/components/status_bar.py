"""
Status Bar Component

Implements Story 2.3 AC6: Real-time performance indicators
- Ollama connection status (🟢🟡🔴)
- Outlook connection status (🟢🟡🔴)
- Processing queue with progress bar
- Token speed display
- Last analysis time
- Real-time updates
"""

import logging
import customtkinter as ctk
from typing import Optional, Callable, Literal, Dict

logger = logging.getLogger(__name__)

ConnectionStatus = Literal["connected", "slow", "disconnected"]


class StatusBar(ctk.CTkFrame):
    """
    Status bar widget showing real-time performance indicators.

    Features:
    - Ollama connection status with clickable indicator
    - Outlook connection status with clickable indicator
    - Processing queue count and progress
    - Token speed from PerformanceTracker
    - Last analysis time
    - Auto-update every 2 seconds
    """

    STATUS_ICONS = {
        "connected": "🟢",
        "slow": "🟡",
        "disconnected": "🔴"
    }

    def __init__(
        self,
        master,
        on_ollama_clicked: Optional[Callable[[], None]] = None,
        on_outlook_clicked: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        """
        Initialize StatusBar.

        Args:
            master: Parent widget
            on_ollama_clicked: Callback when Ollama status is clicked
            on_outlook_clicked: Callback when Outlook status is clicked
        """
        super().__init__(master, height=30, corner_radius=0, **kwargs)

        self.on_ollama_clicked_callback = on_ollama_clicked
        self.on_outlook_clicked_callback = on_outlook_clicked

        # Status tracking
        self.ollama_status: ConnectionStatus = "disconnected"
        self.outlook_status: ConnectionStatus = "disconnected"
        self.queue_count = 0
        self.queue_total = 0
        self.token_speed = 0
        self.last_analysis_time = 0.0

        # Auto-update tracking
        self.update_id = None
        self.auto_update_enabled = False

        # Create widgets
        self._create_widgets()

        logger.debug("StatusBar initialized")

    def _create_widgets(self):
        """Create status bar widgets."""
        # Left side: Connection statuses
        left_frame = ctk.CTkFrame(self, fg_color="transparent")
        left_frame.pack(side="left", fill="y", padx=5)

        # Ollama status
        self.ollama_btn = ctk.CTkButton(
            left_frame,
            text=f"{self.STATUS_ICONS['disconnected']} Ollama: Disconnected",
            font=("Segoe UI", 9),
            width=150,
            height=20,
            fg_color="transparent",
            hover_color=("gray85", "gray25"),
            command=self._on_ollama_clicked
        )
        self.ollama_btn.pack(side="left", padx=2)

        # Outlook status
        self.outlook_btn = ctk.CTkButton(
            left_frame,
            text=f"{self.STATUS_ICONS['disconnected']} Outlook: Disconnected",
            font=("Segoe UI", 9),
            width=150,
            height=20,
            fg_color="transparent",
            hover_color=("gray85", "gray25"),
            command=self._on_outlook_clicked
        )
        self.outlook_btn.pack(side="left", padx=2)

        # Center: Processing queue
        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.pack(side="left", fill="both", expand=True, padx=5)

        self.queue_label = ctk.CTkLabel(
            center_frame,
            text="",
            font=("Segoe UI", 9),
            text_color="gray"
        )
        self.queue_label.pack(side="left", padx=5)

        self.progress_bar = ctk.CTkProgressBar(
            center_frame,
            width=150,
            height=10
        )
        self.progress_bar.set(0)

        # Right side: Performance metrics
        right_frame = ctk.CTkFrame(self, fg_color="transparent")
        right_frame.pack(side="right", fill="y", padx=5)

        self.last_analysis_label = ctk.CTkLabel(
            right_frame,
            text="",
            font=("Segoe UI", 9),
            text_color="gray"
        )
        self.last_analysis_label.pack(side="right", padx=5)

        self.token_speed_label = ctk.CTkLabel(
            right_frame,
            text="",
            font=("Segoe UI", 9),
            text_color="gray"
        )
        self.token_speed_label.pack(side="right", padx=5)

    def set_ollama_status(self, status: ConnectionStatus):
        """
        Set Ollama connection status.

        Args:
            status: Connection status (connected/slow/disconnected)
        """
        self.ollama_status = status
        icon = self.STATUS_ICONS[status]
        status_text = status.title()

        self.ollama_btn.configure(text=f"{icon} Ollama: {status_text}")

        logger.debug(f"Ollama status: {status}")

    def set_outlook_status(self, status: ConnectionStatus):
        """
        Set Outlook connection status.

        Args:
            status: Connection status (connected/slow/disconnected)
        """
        self.outlook_status = status
        icon = self.STATUS_ICONS[status]
        status_text = status.title()

        self.outlook_btn.configure(text=f"{icon} Outlook: {status_text}")

        logger.debug(f"Outlook status: {status}")

    def set_queue_status(self, current: int, total: int):
        """
        Set processing queue status.

        Args:
            current: Current number being processed
            total: Total number in queue
        """
        self.queue_count = current
        self.queue_total = total

        if total > 0:
            # Show queue info and progress bar
            self.queue_label.configure(text=f"Analyzing {current}/{total} emails")
            self.progress_bar.pack(side="left", padx=5)
            self.progress_bar.set(current / total)
        else:
            # Hide queue info
            self.queue_label.configure(text="")
            self.progress_bar.pack_forget()

        logger.debug(f"Queue status: {current}/{total}")

    def set_token_speed(self, tokens_per_sec: int):
        """
        Set token processing speed.

        Args:
            tokens_per_sec: Tokens processed per second
        """
        self.token_speed = tokens_per_sec

        if tokens_per_sec > 0:
            self.token_speed_label.configure(text=f"{tokens_per_sec} tokens/sec")
        else:
            self.token_speed_label.configure(text="")

        logger.debug(f"Token speed: {tokens_per_sec}")

    def set_last_analysis_time(self, seconds: float):
        """
        Set last analysis time.

        Args:
            seconds: Analysis time in seconds
        """
        self.last_analysis_time = seconds

        if seconds > 0:
            self.last_analysis_label.configure(text=f"Last: {seconds:.1f}s")
        else:
            self.last_analysis_label.configure(text="")

        logger.debug(f"Last analysis time: {seconds:.1f}s")

    def _on_ollama_clicked(self):
        """Handle Ollama status button click."""
        if self.on_ollama_clicked_callback:
            self.on_ollama_clicked_callback()

        logger.debug("Ollama status clicked")

    def _on_outlook_clicked(self):
        """Handle Outlook status button click."""
        if self.on_outlook_clicked_callback:
            self.on_outlook_clicked_callback()

        logger.debug("Outlook status clicked")

    def start_auto_update(self, update_callback: Callable[[], Dict]):
        """
        Start auto-updating status every 2 seconds.

        Args:
            update_callback: Callback that returns dict with status updates
                             Expected keys: ollama_status, outlook_status,
                             queue_current, queue_total, token_speed, last_analysis_time
        """
        self.auto_update_enabled = True
        self._update_callback = update_callback
        self._auto_update()

        logger.debug("Started auto-update")

    def _auto_update(self):
        """Perform auto-update."""
        if not self.auto_update_enabled:
            return

        try:
            # Get updated status
            status = self._update_callback()

            # Update all indicators
            if "ollama_status" in status:
                self.set_ollama_status(status["ollama_status"])

            if "outlook_status" in status:
                self.set_outlook_status(status["outlook_status"])

            if "queue_current" in status and "queue_total" in status:
                self.set_queue_status(status["queue_current"], status["queue_total"])

            if "token_speed" in status:
                self.set_token_speed(status["token_speed"])

            if "last_analysis_time" in status:
                self.set_last_analysis_time(status["last_analysis_time"])

        except Exception as e:
            logger.error(f"Auto-update error: {e}")

        # Schedule next update (2 seconds)
        self.update_id = self.after(2000, self._auto_update)

    def stop_auto_update(self):
        """Stop auto-updating."""
        self.auto_update_enabled = False

        if self.update_id:
            self.after_cancel(self.update_id)
            self.update_id = None

        logger.debug("Stopped auto-update")

    def clear(self):
        """Clear all status indicators."""
        self.set_ollama_status("disconnected")
        self.set_outlook_status("disconnected")
        self.set_queue_status(0, 0)
        self.set_token_speed(0)
        self.set_last_analysis_time(0.0)

        logger.debug("Status bar cleared")
