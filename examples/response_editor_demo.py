"""
Response Editor Demo

Demonstrates the Response Editor component functionality.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import customtkinter as ctk
from mailmind.ui.components.response_editor import ResponseEditor


class ResponseEditorDemo(ctk.CTk):
    """Demo application for Response Editor."""

    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Response Editor Demo - Story 2.3")
        self.geometry("800x600")

        # Create response editor
        self.editor = ResponseEditor(
            self,
            on_generate_clicked=self._on_generate,
            on_send_clicked=self._on_send
        )
        self.editor.pack(fill="both", expand=True, padx=20, pady=20)

        # Set sample email context
        self.editor.set_email_context({
            "sender": "John Doe <john@example.com>",
            "subject": "Re: Project Update",
            "body": "Can you provide a status update on the Q4 project?"
        })

    def _on_generate(self, length, tone, template):
        """Handle generate response."""
        print(f"Generate: length={length}, tone={tone}, template={template}")

        # Simulate response generation
        self.editor.show_loading()

        # Simulate delay and generate sample response
        sample_response = f"""Hi John,

Thank you for your email. Here's a {length.lower()} status update on the Q4 project:

The project is progressing well and we're on track to meet the deadline. Key accomplishments this week include completing the initial design phase and beginning development of core features.

Next steps include finalizing the architecture and scheduling the first round of user testing.

Best regards"""

        # Display after "processing"
        self.after(1500, lambda: self.editor.display_generated_response(sample_response))

    def _on_send(self, response_text):
        """Handle send response."""
        print(f"Send: {len(response_text)} characters")
        print("Response sent successfully!")


def main():
    """Run demo."""
    print("Starting Response Editor Demo...")
    print("Features:")
    print("  - Length selector (Brief/Standard/Detailed)")
    print("  - Tone selector (Professional/Friendly/Formal/Casual)")
    print("  - Template dropdown")
    print("  - Generate Response button")
    print("  - Multi-line text editor")
    print("  - Character count")
    print("  - Send and Clear buttons")
    print("\nPress Ctrl+C or close the window to exit")

    app = ResponseEditorDemo()
    app.mainloop()


if __name__ == "__main__":
    main()
