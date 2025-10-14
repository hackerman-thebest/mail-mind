"""
Toast Notification Component

Implements Story 2.3 AC10: Toast notifications
- Success/error/info toasts
- Auto-dismiss
- Manual dismiss
- Toast queue management (max 3 visible)
"""

import logging
import customtkinter as ctk
from typing import Literal

logger = logging.getLogger(__name__)

ToastType = Literal["success", "error", "info"]


class Toast(ctk.CTkFrame):
    """
    Toast notification widget.

    Features:
    - Colored by type (success=green, error=red, info=blue)
    - Auto-dismiss after timeout
    - Click to dismiss
    - Bottom-right positioning
    """

    COLORS = {
        "success": ("#2d5f2d", "#90ee90"),
        "error": ("#5f2d2d", "#ff6b6b"),
        "info": ("#2d3e5f", "#6b9eff")
    }

    def __init__(
        self,
        master,
        message: str,
        toast_type: ToastType = "info",
        duration: int = 3000,
        width: int = 270,
        height: int = 50,
        **kwargs
    ):
        """
        Initialize Toast.

        Args:
            master: Parent widget
            message: Toast message text
            toast_type: Toast type (success, error, info)
            duration: Auto-dismiss duration in milliseconds
            width: Toast width in pixels
            height: Toast height in pixels
        """
        super().__init__(master, width=width, height=height, **kwargs)

        self.message = message
        self.toast_type = toast_type
        self.duration = duration
        self._dismiss_id = None

        # Configure colors
        bg_color, text_color = self.COLORS.get(toast_type, self.COLORS["info"])
        self.configure(fg_color=bg_color, corner_radius=5)

        # Create UI
        self._create_widgets(text_color)

        # Auto-dismiss
        if duration > 0:
            self._dismiss_id = self.after(duration, self.dismiss)

        # Click to dismiss
        self.bind("<Button-1>", lambda e: self.dismiss())

        logger.debug(f"Toast created: {toast_type} - {message}")

    def _create_widgets(self, text_color: str):
        """Create toast widgets."""
        ctk.CTkLabel(
            self,
            text=self.message,
            text_color=text_color,
            font=("Segoe UI", 10),
            wraplength=250
        ).pack(padx=15, pady=10)

    def dismiss(self):
        """Dismiss toast."""
        if self._dismiss_id:
            self.after_cancel(self._dismiss_id)
            self._dismiss_id = None

        self.destroy()
        logger.debug(f"Toast dismissed: {self.message}")


class ToastManager:
    """
    Manages toast notifications with queue limit.

    Features:
    - Max 3 visible toasts
    - FIFO queue
    - Auto-positioning
    """

    MAX_TOASTS = 3

    def __init__(self, root_window):
        """
        Initialize ToastManager.

        Args:
            root_window: Root window for positioning toasts
        """
        self.root = root_window
        self.toasts = []

        logger.debug("ToastManager initialized")

    def show(self, message: str, toast_type: ToastType = "info", duration: int = 3000):
        """
        Show toast notification.

        Args:
            message: Toast message
            toast_type: Toast type (success, error, info)
            duration: Auto-dismiss duration (ms)
        """
        # Remove oldest toast if at limit
        if len(self.toasts) >= self.MAX_TOASTS:
            oldest = self.toasts.pop(0)
            oldest.dismiss()

        # Create toast
        toast = Toast(
            self.root,
            message=message,
            toast_type=toast_type,
            duration=duration,
            width=270,
            height=50
        )

        # Position toast (bottom-right, stacked)
        x_offset = self.root.winfo_width() - 280
        y_offset = self.root.winfo_height() - 80 - (len(self.toasts) * 60)

        toast.place(x=x_offset, y=y_offset)

        self.toasts.append(toast)

        # Remove from list when dismissed
        toast.bind("<Destroy>", lambda e: self._on_toast_destroyed(toast))

    def _on_toast_destroyed(self, toast):
        """Handle toast destruction."""
        if toast in self.toasts:
            self.toasts.remove(toast)

    def clear(self):
        """Dismiss all toasts."""
        for toast in self.toasts[:]:
            toast.dismiss()
        self.toasts = []
