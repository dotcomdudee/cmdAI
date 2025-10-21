"""Input box component for message entry."""
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Input, Button
from textual.message import Message


class InputBox(Horizontal):
    """Message input box with send button."""

    class SendMessage(Message):
        """Message sent when user submits input."""

        def __init__(self, text: str):
            super().__init__()
            self.text = text

    def compose(self) -> ComposeResult:
        """Compose the input box layout."""
        yield Input(
            placeholder="Type your message... (Enter to send, Shift+Enter for newline)",
            id="message-input"
        )
        yield Button("Send", id="send-btn", variant="success")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        if event.input.id == "message-input":
            text = event.input.value.strip()
            if text:
                self.post_message(self.SendMessage(text))
                event.input.value = ""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle send button press."""
        if event.button.id == "send-btn":
            input_widget = self.query_one("#message-input", Input)
            text = input_widget.value.strip()
            if text:
                self.post_message(self.SendMessage(text))
                input_widget.value = ""

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the input box."""
        input_widget = self.query_one("#message-input", Input)
        button = self.query_one("#send-btn", Button)
        input_widget.disabled = not enabled
        button.disabled = not enabled

    def focus_input(self) -> None:
        """Focus the input field."""
        input_widget = self.query_one("#message-input", Input)
        input_widget.focus()
