"""Sidebar component for model selection and conversation list."""
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Button, Label, ListView, ListItem, Static
from textual.binding import Binding
from textual.message import Message

from ..models.conversation import Conversation


class ConversationListItem(ListItem):
    """A list item representing a conversation."""

    def __init__(self, conversation: Conversation):
        super().__init__()
        self.conversation = conversation


class Sidebar(Container):
    """Sidebar with model selector and conversation list."""

    BINDINGS = [
        Binding("n", "new_conversation", "New Chat", show=True),
        Binding("m", "change_model", "Change Model", show=True),
        Binding("d", "delete_selected", "Delete", show=True),
        Binding("ctrl+d", "clear_all", "Clear All", show=True),
    ]

    class NewConversation(Message):
        """Message to request a new conversation."""

    class SelectConversation(Message):
        """Message when a conversation is selected."""

        def __init__(self, conversation: Conversation):
            super().__init__()
            self.conversation = conversation

    class ChangeModel(Message):
        """Message to request model change."""

    class DeleteConversation(Message):
        """Message to request conversation deletion."""

        def __init__(self, conversation: Conversation):
            super().__init__()
            self.conversation = conversation

    class ClearAllConversations(Message):
        """Message to request clearing all conversations."""

    def __init__(self, current_model: str):
        super().__init__()
        self.current_model = current_model
        self.selected_conversation = None

    def compose(self) -> ComposeResult:
        """Compose the sidebar layout."""
        with Vertical(id="sidebar-content"):
            yield Static("WELCOME TO CMDAI", id="sidebar-header", classes="header")
            yield Button("New Conversation", id="new-conv-btn", variant="primary")
            yield Button(f"Model: {self.current_model}", id="model-display-btn")
            yield ListView(id="conversation-list")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "new-conv-btn":
            self.post_message(self.NewConversation())
        elif event.button.id == "model-display-btn":
            self.post_message(self.ChangeModel())

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle conversation selection."""
        if isinstance(event.item, ConversationListItem):
            self.selected_conversation = event.item.conversation
            self.post_message(self.SelectConversation(event.item.conversation))

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Track highlighted conversation."""
        if isinstance(event.item, ConversationListItem):
            self.selected_conversation = event.item.conversation

    def update_conversations(self, conversations: list[Conversation]) -> None:
        """Update the conversation list."""
        list_view = self.query_one("#conversation-list", ListView)
        list_view.clear()

        for conv in conversations:
            item = ConversationListItem(conv)
            # Create a label with conversation title and date with more spacing
            date_str = conv.updated_at.strftime("%m/%d %H:%M")
            label = Static(f"{conv.title}\n\n[dim]{date_str}[/dim]")
            item._add_child(label)
            list_view.append(item)

    def update_model(self, model: str) -> None:
        """Update the displayed model."""
        self.current_model = model
        model_button = self.query_one("#model-display-btn", Button)
        model_button.label = f"Model: {model}"

    def action_new_conversation(self) -> None:
        """Action to create new conversation."""
        self.post_message(self.NewConversation())

    def action_change_model(self) -> None:
        """Action to change model."""
        self.post_message(self.ChangeModel())

    def action_delete_selected(self) -> None:
        """Action to delete selected conversation."""
        if self.selected_conversation:
            self.post_message(self.DeleteConversation(self.selected_conversation))

    def action_clear_all(self) -> None:
        """Action to clear all conversations."""
        self.post_message(self.ClearAllConversations())
