"""Chat view component with markdown rendering."""
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static
from rich.markdown import Markdown
from rich.syntax import Syntax
from datetime import datetime

from ..models.message import Message


class MessageWidget(Static):
    """Widget to display a single message."""

    def __init__(self, message: Message):
        super().__init__()
        self.message = message
        self.update_content()

    def update_content(self) -> None:
        """Update the message content display."""
        # Style based on role
        if self.message.role == "user":
            self.add_class("user-message")
            self.remove_class("assistant-message")
            prefix = "You"
        else:
            self.add_class("assistant-message")
            self.remove_class("user-message")
            model_info = f" ({self.message.model})" if self.message.model else ""
            prefix = f"cmdAI{model_info}"

        # Create markdown content
        content = f"**{prefix}**\n\n{self.message.content}"
        self.update(Markdown(content))


class StreamingMessageWidget(Static):
    """Widget for displaying a message as it streams in."""

    def __init__(self, chat_view: "ChatView"):
        super().__init__()
        self.chat_view = chat_view
        self.add_class("assistant-message")
        self.content_buffer = ""
        self.update("**cmdAI**\n\n_Thinking..._")

    def append_content(self, text: str) -> None:
        """Append text to the streaming message."""
        self.content_buffer += text
        self.update(Markdown(f"**cmdAI**\n\n{self.content_buffer}"))
        # Only auto-scroll if user is already at the bottom
        self.chat_view.scroll_to_bottom_if_near()

    def finalize(self, model: str | None = None) -> Message:
        """Finalize the streaming message and return as Message object."""
        model_info = f" ({model})" if model else ""
        self.update(Markdown(f"**cmdAI{model_info}**\n\n{self.content_buffer}"))
        return Message(
            role="assistant",
            content=self.content_buffer,
            timestamp=datetime.now(),
            model=model,
        )


class ChatView(VerticalScroll):
    """Main chat view with message display."""

    def compose(self) -> ComposeResult:
        """Compose the chat view."""
        yield Static("Start a conversation by typing a message below.", id="welcome-message")

    def is_at_bottom(self) -> bool:
        """Check if the view is scrolled to the bottom."""
        # Consider "at bottom" if within 3 lines of the actual bottom
        return self.scroll_offset.y >= (self.max_scroll_y - 3)

    def scroll_to_bottom_if_near(self) -> None:
        """Scroll to bottom only if already near the bottom."""
        if self.is_at_bottom():
            self.scroll_end(animate=False)

    def add_message(self, message: Message) -> None:
        """Add a message to the chat view."""
        # Remove welcome message if present
        try:
            welcome = self.query_one("#welcome-message")
            welcome.remove()
        except Exception:
            pass

        widget = MessageWidget(message)
        self.mount(widget)
        self.scroll_end(animate=False)

    def create_streaming_message(self) -> StreamingMessageWidget:
        """Create and mount a streaming message widget."""
        widget = StreamingMessageWidget(self)
        self.mount(widget)
        self.scroll_end(animate=False)
        return widget

    def clear_messages(self) -> None:
        """Clear all messages from the view."""
        for child in list(self.children):
            child.remove()
        # Only add welcome message if not already present
        try:
            self.query_one("#welcome-message")
        except Exception:
            self.mount(Static("Start a conversation by typing a message below.", id="welcome-message"))

    def load_messages(self, messages: list[Message]) -> None:
        """Load a list of messages into the view."""
        self.clear_messages()
        if messages:
            for message in messages:
                self.add_message(message)
