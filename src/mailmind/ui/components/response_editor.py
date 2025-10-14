"""
Response Editor Component

Implements Story 2.3 AC5: Response editor with draft generation
- Multi-line text editor for composing replies
- Generate Response button with length dropdown
- Tone selector (Professional/Friendly/Formal/Casual)
- Template dropdown
- Loading indicators
- Send button for Outlook integration
"""

import logging
import customtkinter as ctk
from typing import Optional, Callable, Dict

logger = logging.getLogger(__name__)


class ResponseEditor(ctk.CTkFrame):
    """
    Response editor widget for composing email replies.

    Features:
    - Multi-line text editor
    - Response length options (Brief/Standard/Detailed)
    - Tone selector (Professional/Friendly/Formal/Casual)
    - Template dropdown
    - Draft generation with loading state
    - Send button
    - Integration with ResponseGenerator
    """

    # Response length options
    RESPONSE_LENGTHS = ["Brief", "Standard", "Detailed"]

    # Tone options
    TONES = ["Professional", "Friendly", "Formal", "Casual"]

    # Template options
    TEMPLATES = [
        "None (Custom)",
        "Meeting Acceptance",
        "Meeting Decline",
        "Status Update",
        "Thank You",
        "Follow-up",
        "Request Information",
        "Acknowledge Receipt"
    ]

    def __init__(
        self,
        master,
        on_generate_clicked: Optional[Callable[[str, str, str], None]] = None,
        on_send_clicked: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        """
        Initialize ResponseEditor.

        Args:
            master: Parent widget
            on_generate_clicked: Callback when Generate Response is clicked (length, tone, template)
            on_send_clicked: Callback when Send is clicked (response_text)
        """
        super().__init__(master, **kwargs)

        self.on_generate_clicked_callback = on_generate_clicked
        self.on_send_clicked_callback = on_send_clicked

        self.is_generating = False
        self.current_email = None

        # Create UI
        self._create_widgets()

        logger.debug("ResponseEditor initialized")

    def _create_widgets(self):
        """Create editor widgets."""
        # Header
        header = ctk.CTkLabel(
            self,
            text="Response Composer",
            font=("Segoe UI", 14, "bold")
        )
        header.pack(pady=10, padx=10, anchor="w")

        # Controls frame
        controls_frame = ctk.CTkFrame(self)
        controls_frame.pack(fill="x", padx=10, pady=5)

        # Row 1: Length and Tone
        row1 = ctk.CTkFrame(controls_frame, fg_color="transparent")
        row1.pack(fill="x", pady=2)

        ctk.CTkLabel(
            row1,
            text="Length:",
            font=("Segoe UI", 10)
        ).pack(side="left", padx=5)

        self.length_var = ctk.StringVar(value="Standard")
        self.length_menu = ctk.CTkOptionMenu(
            row1,
            variable=self.length_var,
            values=self.RESPONSE_LENGTHS,
            width=120
        )
        self.length_menu.pack(side="left", padx=5)

        ctk.CTkLabel(
            row1,
            text="Tone:",
            font=("Segoe UI", 10)
        ).pack(side="left", padx=5)

        self.tone_var = ctk.StringVar(value="Professional")
        self.tone_menu = ctk.CTkOptionMenu(
            row1,
            variable=self.tone_var,
            values=self.TONES,
            width=120
        )
        self.tone_menu.pack(side="left", padx=5)

        # Row 2: Template and Generate button
        row2 = ctk.CTkFrame(controls_frame, fg_color="transparent")
        row2.pack(fill="x", pady=2)

        ctk.CTkLabel(
            row2,
            text="Template:",
            font=("Segoe UI", 10)
        ).pack(side="left", padx=5)

        self.template_var = ctk.StringVar(value="None (Custom)")
        self.template_menu = ctk.CTkOptionMenu(
            row2,
            variable=self.template_var,
            values=self.TEMPLATES,
            width=180
        )
        self.template_menu.pack(side="left", padx=5)

        self.generate_btn = ctk.CTkButton(
            row2,
            text="⚡ Generate Response",
            command=self._on_generate_clicked,
            width=150
        )
        self.generate_btn.pack(side="right", padx=5)

        # Text editor
        editor_frame = ctk.CTkFrame(self)
        editor_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.text_editor = ctk.CTkTextbox(
            editor_frame,
            font=("Segoe UI", 11),
            wrap="word"
        )
        self.text_editor.pack(fill="both", expand=True, padx=5, pady=5)

        # Placeholder text
        self.text_editor.insert("1.0", "Click 'Generate Response' to create a draft, or type your response here...")
        self.text_editor.configure(text_color="gray")

        # Bind focus events for placeholder
        self.text_editor.bind("<FocusIn>", self._on_focus_in)
        self.text_editor.bind("<FocusOut>", self._on_focus_out)

        # Loading indicator frame (hidden by default)
        self.loading_frame = ctk.CTkFrame(self)
        self.loading_label = ctk.CTkLabel(
            self.loading_frame,
            text="⏳ Generating response...",
            font=("Segoe UI", 11),
            text_color="gray"
        )

        # Action buttons frame
        actions_frame = ctk.CTkFrame(self)
        actions_frame.pack(fill="x", padx=10, pady=10)

        # Character count
        self.char_count_label = ctk.CTkLabel(
            actions_frame,
            text="0 characters",
            font=("Segoe UI", 9),
            text_color="gray"
        )
        self.char_count_label.pack(side="left", padx=5)

        # Clear button
        self.clear_btn = ctk.CTkButton(
            actions_frame,
            text="Clear",
            command=self._on_clear_clicked,
            width=80,
            fg_color="transparent",
            border_width=1
        )
        self.clear_btn.pack(side="left", padx=5)

        # Send button
        self.send_btn = ctk.CTkButton(
            actions_frame,
            text="📧 Send Reply",
            command=self._on_send_clicked,
            width=120,
            state="disabled"
        )
        self.send_btn.pack(side="right", padx=5)

        # Bind text changes for character count
        self.text_editor.bind("<KeyRelease>", self._update_char_count)

    def _on_focus_in(self, event):
        """Handle focus in event (remove placeholder)."""
        current_text = self.text_editor.get("1.0", "end-1c")
        if current_text.startswith("Click 'Generate Response'"):
            self.text_editor.delete("1.0", "end")
            self.text_editor.configure(text_color=("black", "white"))

    def _on_focus_out(self, event):
        """Handle focus out event (restore placeholder if empty)."""
        current_text = self.text_editor.get("1.0", "end-1c").strip()
        if not current_text:
            self.text_editor.delete("1.0", "end")
            self.text_editor.insert("1.0", "Click 'Generate Response' to create a draft, or type your response here...")
            self.text_editor.configure(text_color="gray")

    def _update_char_count(self, event=None):
        """Update character count label."""
        current_text = self.text_editor.get("1.0", "end-1c")
        # Don't count placeholder text
        if current_text.startswith("Click 'Generate Response'"):
            count = 0
        else:
            count = len(current_text)

        self.char_count_label.configure(text=f"{count} characters")

        # Enable/disable send button
        if count > 0:
            self.send_btn.configure(state="normal")
        else:
            self.send_btn.configure(state="disabled")

    def _on_generate_clicked(self):
        """Handle Generate Response button click."""
        length = self.length_var.get()
        tone = self.tone_var.get()
        template = self.template_var.get()

        logger.debug(f"Generate clicked: length={length}, tone={tone}, template={template}")

        # Show loading
        self.show_loading("Generating response...")

        # Call callback
        if self.on_generate_clicked_callback:
            self.on_generate_clicked_callback(length, tone, template)

    def _on_send_clicked(self):
        """Handle Send button click."""
        response_text = self.text_editor.get("1.0", "end-1c")

        # Don't send if empty or placeholder
        if not response_text.strip() or response_text.startswith("Click 'Generate Response'"):
            logger.warning("Cannot send empty response")
            return

        logger.debug(f"Send clicked: {len(response_text)} characters")

        # Call callback
        if self.on_send_clicked_callback:
            self.on_send_clicked_callback(response_text)

    def _on_clear_clicked(self):
        """Handle Clear button click."""
        self.text_editor.delete("1.0", "end")
        self.text_editor.insert("1.0", "Click 'Generate Response' to create a draft, or type your response here...")
        self.text_editor.configure(text_color="gray")
        self._update_char_count()

        logger.debug("Editor cleared")

    def set_email_context(self, email: Dict):
        """
        Set the email context for response generation.

        Args:
            email: Email dict with sender, subject, body, etc.
        """
        self.current_email = email
        logger.debug(f"Email context set: {email.get('subject', 'Unknown')}")

    def display_generated_response(self, response_text: str):
        """
        Display generated response in editor.

        Args:
            response_text: Generated response text
        """
        self.is_generating = False
        self.hide_loading()

        # Clear editor and insert generated text
        self.text_editor.delete("1.0", "end")
        self.text_editor.insert("1.0", response_text)
        self.text_editor.configure(text_color=("black", "white"))

        # Update char count
        self._update_char_count()

        logger.debug(f"Displayed generated response: {len(response_text)} characters")

    def show_loading(self, message: str = "Generating response..."):
        """Show loading state."""
        self.is_generating = True

        # Disable controls
        self.generate_btn.configure(state="disabled", text="⏳ Generating...")
        self.length_menu.configure(state="disabled")
        self.tone_menu.configure(state="disabled")
        self.template_menu.configure(state="disabled")
        self.text_editor.configure(state="disabled")
        self.send_btn.configure(state="disabled")
        self.clear_btn.configure(state="disabled")

        logger.debug(f"Showing loading: {message}")

    def hide_loading(self):
        """Hide loading state."""
        self.is_generating = False

        # Re-enable controls
        self.generate_btn.configure(state="normal", text="⚡ Generate Response")
        self.length_menu.configure(state="normal")
        self.tone_menu.configure(state="normal")
        self.template_menu.configure(state="normal")
        self.text_editor.configure(state="normal")
        self.clear_btn.configure(state="normal")

        # Send button state depends on text content
        self._update_char_count()

        logger.debug("Loading hidden")

    def show_error(self, error_message: str):
        """
        Show error message.

        Args:
            error_message: Error message to display
        """
        self.is_generating = False
        self.hide_loading()

        # Display error in editor
        self.text_editor.delete("1.0", "end")
        self.text_editor.insert("1.0", f"❌ Error generating response:\n\n{error_message}\n\nPlease try again.")
        self.text_editor.configure(text_color="#F44336")

        logger.debug(f"Showing error: {error_message}")

    def clear(self):
        """Clear the editor."""
        self._on_clear_clicked()

    def get_response_text(self) -> str:
        """Get current response text."""
        text = self.text_editor.get("1.0", "end-1c")
        # Return empty if placeholder
        if text.startswith("Click 'Generate Response'"):
            return ""
        return text
