"""
Unit tests for ResponseEditor component.

Tests Story 2.3 AC5: Response editor with draft generation
"""

import pytest
import customtkinter as ctk
from unittest.mock import Mock, patch

from mailmind.ui.components.response_editor import ResponseEditor


@pytest.fixture
def root():
    """Create root window for tests."""
    root = ctk.CTk()
    yield root
    root.destroy()


@pytest.fixture
def editor(root):
    """Create ResponseEditor for tests."""
    return ResponseEditor(root)


@pytest.fixture
def sample_email():
    """Create sample email data."""
    return {
        "subject": "Project Update Meeting",
        "sender": "john.doe@example.com",
        "body": "Can we schedule a meeting next week?",
        "timestamp": "2025-10-14 10:00:00"
    }


class TestResponseEditorInitialization:
    """Test ResponseEditor initialization."""

    def test_initialization(self, root):
        """Test editor initializes correctly."""
        editor = ResponseEditor(root)

        assert editor.on_generate_clicked_callback is None
        assert editor.on_send_clicked_callback is None
        assert editor.is_generating is False
        assert editor.current_email is None

    def test_initialization_with_callbacks(self, root):
        """Test editor initializes with callbacks."""
        generate_cb = Mock()
        send_cb = Mock()
        editor = ResponseEditor(root, on_generate_clicked=generate_cb, on_send_clicked=send_cb)

        assert editor.on_generate_clicked_callback == generate_cb
        assert editor.on_send_clicked_callback == send_cb

    def test_dropdown_defaults(self, editor):
        """Test dropdown menus have correct defaults."""
        assert editor.length_var.get() == "Standard"
        assert editor.tone_var.get() == "Professional"
        assert editor.template_var.get() == "None (Custom)"

    def test_dropdown_options(self, editor):
        """Test dropdown menus have all options."""
        assert editor.RESPONSE_LENGTHS == ["Brief", "Standard", "Detailed"]
        assert editor.TONES == ["Professional", "Friendly", "Formal", "Casual"]
        assert len(editor.TEMPLATES) == 8
        assert "Meeting Acceptance" in editor.TEMPLATES
        assert "Thank You" in editor.TEMPLATES


class TestResponseEditorControls:
    """Test response editor controls."""

    def test_length_selection(self, editor):
        """Test changing length selection."""
        editor.length_var.set("Brief")
        assert editor.length_var.get() == "Brief"

        editor.length_var.set("Detailed")
        assert editor.length_var.get() == "Detailed"

    def test_tone_selection(self, editor):
        """Test changing tone selection."""
        editor.tone_var.set("Friendly")
        assert editor.tone_var.get() == "Friendly"

        editor.tone_var.set("Formal")
        assert editor.tone_var.get() == "Formal"

    def test_template_selection(self, editor):
        """Test changing template selection."""
        editor.template_var.set("Meeting Acceptance")
        assert editor.template_var.get() == "Meeting Acceptance"

        editor.template_var.set("Thank You")
        assert editor.template_var.get() == "Thank You"


class TestResponseEditorTextInput:
    """Test text editor functionality."""

    def test_placeholder_text_on_init(self, editor):
        """Test editor shows placeholder text initially."""
        text = editor.text_editor.get("1.0", "end-1c")
        assert text.startswith("Click 'Generate Response'")

    def test_clear_placeholder_on_focus(self, editor):
        """Test placeholder is cleared on focus."""
        # Simulate focus in
        editor._on_focus_in(None)

        text = editor.text_editor.get("1.0", "end-1c")
        assert text == ""

    def test_restore_placeholder_on_blur_if_empty(self, editor):
        """Test placeholder is restored on blur if empty."""
        # Clear placeholder
        editor._on_focus_in(None)

        # Simulate focus out with empty content
        editor._on_focus_out(None)

        text = editor.text_editor.get("1.0", "end-1c")
        assert text.startswith("Click 'Generate Response'")

    def test_keep_content_on_blur_if_not_empty(self, editor):
        """Test content is kept on blur if not empty."""
        # Clear placeholder and add content
        editor._on_focus_in(None)
        editor.text_editor.insert("1.0", "Test response")

        # Simulate focus out
        editor._on_focus_out(None)

        text = editor.text_editor.get("1.0", "end-1c")
        assert text == "Test response"

    def test_insert_text(self, editor):
        """Test inserting text into editor."""
        editor.text_editor.delete("1.0", "end")
        editor.text_editor.insert("1.0", "Hello, this is a test response.")

        text = editor.text_editor.get("1.0", "end-1c")
        assert text == "Hello, this is a test response."


class TestResponseEditorCharacterCount:
    """Test character count functionality."""

    def test_char_count_initial(self, editor):
        """Test initial character count is 0."""
        count_text = editor.char_count_label.cget("text")
        assert "0 characters" in count_text

    def test_char_count_updates(self, editor):
        """Test character count updates with text."""
        editor.text_editor.delete("1.0", "end")
        editor.text_editor.insert("1.0", "Test response")
        editor._update_char_count()

        count_text = editor.char_count_label.cget("text")
        assert "13 characters" in count_text

    def test_char_count_ignores_placeholder(self, editor):
        """Test character count doesn't count placeholder text."""
        # Editor has placeholder initially
        editor._update_char_count()

        count_text = editor.char_count_label.cget("text")
        assert "0 characters" in count_text


class TestResponseEditorSendButton:
    """Test send button functionality."""

    def test_send_button_disabled_initially(self, editor):
        """Test send button is disabled when editor is empty."""
        assert editor.send_btn.cget("state") == "disabled"

    def test_send_button_enabled_with_text(self, editor):
        """Test send button is enabled when editor has text."""
        editor.text_editor.delete("1.0", "end")
        editor.text_editor.insert("1.0", "Test response")
        editor._update_char_count()

        assert editor.send_btn.cget("state") == "normal"

    def test_send_button_callback(self, root):
        """Test send button triggers callback."""
        callback = Mock()
        editor = ResponseEditor(root, on_send_clicked=callback)

        # Add text
        editor.text_editor.delete("1.0", "end")
        editor.text_editor.insert("1.0", "Test response to send")

        # Click send
        editor._on_send_clicked()

        callback.assert_called_once_with("Test response to send")

    def test_send_button_no_callback(self, editor):
        """Test send button with no callback doesn't crash."""
        editor.text_editor.delete("1.0", "end")
        editor.text_editor.insert("1.0", "Test response")

        # Should not crash
        editor._on_send_clicked()

    def test_send_button_ignores_placeholder(self, editor):
        """Test send button doesn't send placeholder text."""
        callback = Mock()
        editor.on_send_clicked_callback = callback

        # Editor has placeholder
        editor._on_send_clicked()

        # Callback should not be called
        callback.assert_not_called()


class TestResponseEditorClearButton:
    """Test clear button functionality."""

    def test_clear_button_clears_text(self, editor):
        """Test clear button clears editor text."""
        # Add text
        editor.text_editor.delete("1.0", "end")
        editor.text_editor.insert("1.0", "Text to clear")

        # Click clear
        editor._on_clear_clicked()

        # Should restore placeholder
        text = editor.text_editor.get("1.0", "end-1c")
        assert text.startswith("Click 'Generate Response'")

    def test_clear_button_resets_char_count(self, editor):
        """Test clear button resets character count."""
        # Add text
        editor.text_editor.delete("1.0", "end")
        editor.text_editor.insert("1.0", "Text to clear")
        editor._update_char_count()

        # Click clear
        editor._on_clear_clicked()

        # Char count should be 0
        count_text = editor.char_count_label.cget("text")
        assert "0 characters" in count_text

    def test_clear_method(self, editor):
        """Test clear() method works."""
        editor.text_editor.delete("1.0", "end")
        editor.text_editor.insert("1.0", "Text to clear")

        editor.clear()

        text = editor.text_editor.get("1.0", "end-1c")
        assert text.startswith("Click 'Generate Response'")


class TestResponseEditorGenerateButton:
    """Test generate button functionality."""

    def test_generate_button_callback(self, root):
        """Test generate button triggers callback with correct args."""
        callback = Mock()
        editor = ResponseEditor(root, on_generate_clicked=callback)

        # Set dropdown values
        editor.length_var.set("Brief")
        editor.tone_var.set("Friendly")
        editor.template_var.set("Thank You")

        # Click generate
        editor._on_generate_clicked()

        callback.assert_called_once_with("Brief", "Friendly", "Thank You")

    def test_generate_button_no_callback(self, editor):
        """Test generate button with no callback doesn't crash."""
        # Should not crash
        editor._on_generate_clicked()

    def test_generate_button_shows_loading(self, editor):
        """Test generate button triggers loading state."""
        editor._on_generate_clicked()

        assert editor.is_generating is True
        assert editor.generate_btn.cget("state") == "disabled"


class TestResponseEditorLoadingState:
    """Test loading state functionality."""

    def test_show_loading_default(self, editor):
        """Test show_loading with default message."""
        editor.show_loading()

        assert editor.is_generating is True
        assert editor.generate_btn.cget("state") == "disabled"
        assert editor.length_menu.cget("state") == "disabled"
        assert editor.tone_menu.cget("state") == "disabled"
        assert editor.template_menu.cget("state") == "disabled"
        # Note: CTkTextbox doesn't support cget("state"), so we can't test it
        assert editor.send_btn.cget("state") == "disabled"
        assert editor.clear_btn.cget("state") == "disabled"

    def test_show_loading_custom_message(self, editor):
        """Test show_loading with custom message."""
        editor.show_loading("Processing your request...")

        assert editor.is_generating is True

    def test_hide_loading(self, editor):
        """Test hide_loading re-enables controls."""
        # First show loading
        editor.show_loading()

        # Then hide
        editor.hide_loading()

        assert editor.is_generating is False
        assert editor.generate_btn.cget("state") == "normal"
        assert editor.length_menu.cget("state") == "normal"
        assert editor.tone_menu.cget("state") == "normal"
        assert editor.template_menu.cget("state") == "normal"
        # Note: CTkTextbox doesn't support cget("state"), so we can't test it
        assert editor.clear_btn.cget("state") == "normal"


class TestResponseEditorGeneratedResponse:
    """Test displaying generated response."""

    def test_display_generated_response(self, editor):
        """Test displaying generated response text."""
        response_text = "Thank you for your email. I will review the proposal and get back to you soon."

        editor.display_generated_response(response_text)

        text = editor.text_editor.get("1.0", "end-1c")
        assert text == response_text
        assert editor.is_generating is False

    def test_display_generated_response_updates_char_count(self, editor):
        """Test displaying response updates character count."""
        response_text = "Short response."

        editor.display_generated_response(response_text)

        count_text = editor.char_count_label.cget("text")
        assert "15 characters" in count_text

    def test_display_generated_response_enables_send(self, editor):
        """Test displaying response enables send button."""
        response_text = "Generated response text."

        editor.display_generated_response(response_text)

        assert editor.send_btn.cget("state") == "normal"


class TestResponseEditorError:
    """Test error display functionality."""

    def test_show_error(self, editor):
        """Test showing error message."""
        editor.show_error("Failed to connect to Ollama")

        text = editor.text_editor.get("1.0", "end-1c")
        assert "❌ Error generating response:" in text
        assert "Failed to connect to Ollama" in text
        assert editor.is_generating is False

    def test_show_error_hides_loading(self, editor):
        """Test error state hides loading."""
        # First show loading
        editor.show_loading()

        # Then show error
        editor.show_error("Test error")

        assert editor.is_generating is False
        assert editor.generate_btn.cget("state") == "normal"


class TestResponseEditorEmailContext:
    """Test email context functionality."""

    def test_set_email_context(self, editor, sample_email):
        """Test setting email context."""
        editor.set_email_context(sample_email)

        assert editor.current_email == sample_email

    def test_set_email_context_updates_reference(self, editor):
        """Test setting different email contexts."""
        email1 = {"subject": "Email 1"}
        email2 = {"subject": "Email 2"}

        editor.set_email_context(email1)
        assert editor.current_email == email1

        editor.set_email_context(email2)
        assert editor.current_email == email2


class TestResponseEditorGetResponse:
    """Test getting response text."""

    def test_get_response_text(self, editor):
        """Test getting response text."""
        editor.text_editor.delete("1.0", "end")
        editor.text_editor.insert("1.0", "My response")

        text = editor.get_response_text()
        assert text == "My response"

    def test_get_response_text_with_placeholder(self, editor):
        """Test getting response text returns empty for placeholder."""
        # Editor has placeholder initially
        text = editor.get_response_text()
        assert text == ""

    def test_get_response_text_empty(self, editor):
        """Test getting empty response text."""
        editor.text_editor.delete("1.0", "end")

        text = editor.get_response_text()
        assert text == ""


class TestResponseEditorEdgeCases:
    """Test edge cases and error handling."""

    def test_generate_with_all_dropdown_combinations(self, editor):
        """Test generate works with all dropdown combinations."""
        callback = Mock()
        editor.on_generate_clicked_callback = callback

        for length in editor.RESPONSE_LENGTHS:
            for tone in editor.TONES:
                editor.length_var.set(length)
                editor.tone_var.set(tone)
                editor._on_generate_clicked()

        # Should have called for each combination
        assert callback.call_count == len(editor.RESPONSE_LENGTHS) * len(editor.TONES)

    def test_long_response_text(self, editor):
        """Test handling very long response text."""
        long_text = "A" * 10000  # 10,000 characters

        editor.display_generated_response(long_text)

        text = editor.text_editor.get("1.0", "end-1c")
        assert text == long_text
        assert "10000 characters" in editor.char_count_label.cget("text")

    def test_empty_email_context(self, editor):
        """Test setting empty email context."""
        editor.set_email_context({})

        assert editor.current_email == {}

    def test_multiple_clear_operations(self, editor):
        """Test multiple clear operations don't break state."""
        editor.clear()
        editor.clear()
        editor.clear()

        # Should still show placeholder
        text = editor.text_editor.get("1.0", "end-1c")
        assert text.startswith("Click 'Generate Response'")

    def test_send_empty_string(self, editor):
        """Test sending empty string is ignored."""
        callback = Mock()
        editor.on_send_clicked_callback = callback

        editor.text_editor.delete("1.0", "end")
        editor._on_send_clicked()

        # Callback should not be called for empty text
        callback.assert_not_called()

    def test_loading_state_preserves_after_hide_show(self, editor):
        """Test loading state can be shown multiple times."""
        editor.show_loading()
        editor.hide_loading()
        editor.show_loading()
        editor.hide_loading()

        # Should be in normal state
        assert editor.is_generating is False
        assert editor.generate_btn.cget("state") == "normal"
