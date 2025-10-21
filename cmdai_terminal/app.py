"""Main cmdAI Terminal application."""
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Footer, Header, Static
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Label, ListItem, ListView, OptionList
from textual.widgets.option_list import Option
from datetime import datetime

from .components.sidebar import Sidebar
from .components.chat_view import ChatView
from .components.input_box import InputBox
from .api.unified_client import UnifiedClient
from .models.conversation import Conversation
from .models.message import Message
from .storage.history import ConversationStorage
from .config import Config


class ModelSelectorScreen(Screen[str | None]):
    """Full-screen model selector."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("q", "cancel", "Cancel"),
    ]

    def __init__(self, models: list[str], current_model: str):
        super().__init__()
        self.models = models if models else ["llama2"]
        self.current_model = current_model

    def compose(self) -> ComposeResult:
        """Compose the model selector screen."""
        yield Header()
        with Vertical(id="model-selector-outer"):
            with Vertical(id="model-selector-container"):
                yield Static("=" * 50, id="separator-top")
                yield Static(f"SELECT A MODEL", id="model-screen-title")
                yield Static(f"Available models: {len(self.models)}", id="model-screen-subtitle")
                yield Static("=" * 50, id="separator-mid")

                # Create option list with models
                options = []
                for i, m in enumerate(self.models, 1):
                    prefix = "✓ " if m == self.current_model else f"{i}."
                    # Add emoji indicator for provider
                    display_name = m
                    if m.startswith("openai/"):
                        display_name = f"⭐ {m}"  # OpenAI models get star emoji
                    else:
                        display_name = f"🦙 {m}"  # Ollama models get llama emoji
                    options.append(Option(f"{prefix} {display_name}", id=m))

                yield OptionList(*options, id="model-options")
                yield Static("-" * 50, id="separator-bottom")
                yield Static("↑/↓: Navigate | Enter: Select | Esc/Q: Cancel", id="model-screen-hint")
        yield Footer()

    def on_mount(self) -> None:
        """Focus the option list when mounted."""
        self.title = "Model Selection"
        self.sub_title = ""
        option_list = self.query_one("#model-options", OptionList)
        # Select the current model by default
        try:
            current_index = self.models.index(self.current_model)
            option_list.highlighted = current_index
        except (ValueError, IndexError):
            pass
        option_list.focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle model selection."""
        selected_model = event.option.id
        if selected_model:
            self.dismiss(selected_model)

    def action_cancel(self) -> None:
        """Cancel selection and return to main screen."""
        self.dismiss(None)


class CmdAITerminalApp(App):
    """cmdAI Terminal - Beautiful Ollama API client."""

    ENABLE_COMMAND_PALETTE = False

    CSS = """
    /* cmdAI Theme - Custom Dark Theme */
    * {
        /* Base colors */
        background: #171717;
        color: #e0e0e0;

        /* Scrollbar colors using Textual design tokens */
        scrollbar-background: #262626;
        scrollbar-background-hover: #262626;
        scrollbar-background-active: #262626;
        scrollbar-color: #757575;
        scrollbar-color-hover: #757575;
        scrollbar-color-active: #757575;
    }

    Screen {
        layout: vertical;
        background: #171717;
    }

    #main-container {
        layout: horizontal;
        height: 1fr;
    }

    Sidebar {
        width: 35;
        background: #1f1f1f;
        border-right: solid #262626;
    }

    #sidebar-content {
        height: 100%;
        padding: 1;
        background: #1f1f1f;
    }

    #sidebar-header {
        text-align: center;
        text-style: bold;
        color: #e0e0e0;
        margin-bottom: 1;
        background: transparent;
    }

    .section-title {
        text-style: bold;
        margin-top: 1;
        margin-bottom: 1;
        color: #757575;
    }

    #model-display-btn {
        width: 100%;
        margin-bottom: 1;
        background: #262626;
        color: #e0e0e0;
        border: solid #262626;
        text-align: center;
    }

    #model-display-btn:hover {
        background: #757575;
    }

    #model-display-btn:focus {
        border: solid #757575;
    }

    #conversation-list {
        height: 1fr;
        border: solid #262626;
        background: #171717;
    }

    #conversation-list > ListItem {
        background: #1f1f1f;
        color: #e0e0e0;
        padding: 1;
        margin: 0 0 1 0;
    }

    #conversation-list > ListItem > Static {
        background: transparent;
        color: #e0e0e0;
    }

    #conversation-list > ListItem:hover {
        background: #262626;
    }

    #conversation-list > ListItem.-highlight {
        background: #262626;
    }

    /* Scrollbar styling for chat view */
    ChatView > ScrollBar {
        background: #1f1f1f;
    }

    ChatView > ScrollBar > .scrollbar--thumb {
        background: #757575;
    }

    ChatView > ScrollBar > .scrollbar--thumb:hover {
        background: #757575;
    }

    #chat-container {
        width: 1fr;
        height: 1fr;
        layout: vertical;
        background: #171717;
    }

    ChatView {
        height: 1fr;
        padding: 1 2;
        background: #171717;
    }

    .user-message {
        background: #1f1f1f;
        padding: 1 2;
        margin: 1 0;
        border-left: thick #757575;
        color: #e0e0e0;
    }

    .assistant-message {
        background: #1f1f1f;
        padding: 1 2;
        margin: 1 0;
        border-left: thick #757575;
        color: #e0e0e0;
    }

    InputBox {
        height: auto;
        padding: 1;
        background: #1f1f1f;
        border-top: solid #262626;
    }

    #message-input {
        width: 1fr;
        background: #262626;
        color: #e0e0e0;
        border: solid #262626;
    }

    #message-input > .input--placeholder {
        background: transparent;
        color: #757575;
    }

    #message-input > .input--cursor {
        background: #e0e0e0;
    }

    #message-input:focus {
        border: solid #757575;
    }

    #send-btn {
        width: auto;
        margin-left: 1;
        background: #262626;
        color: #e0e0e0;
        border: solid #262626;
    }

    #send-btn:hover {
        background: #757575;
        border: solid #757575;
    }

    Button {
        width: 100%;
        margin-bottom: 1;
        background: #262626;
        color: #e0e0e0;
        border: solid #262626;
    }

    Button:hover {
        background: #757575;
    }

    Button:focus {
        border: solid #757575;
    }

    ModelSelectorScreen {
        background: #171717;
    }

    #model-selector-outer {
        align: center middle;
        width: 100%;
        height: 1fr;
        background: #171717;
    }

    #model-selector-container {
        width: 80;
        height: auto;
        background: #171717;
    }

    #model-screen-title {
        text-align: center;
        text-style: bold;
        color: #e0e0e0;
        padding: 1;
        width: 100%;
    }

    #model-screen-subtitle {
        text-align: center;
        color: #757575;
        padding: 0 0 1 0;
        width: 100%;
    }

    #separator-top, #separator-mid, #separator-bottom {
        text-align: center;
        color: #262626;
        width: 100%;
        padding: 0;
        margin: 0;
    }

    #model-options {
        height: 1fr;
        max-height: 30;
        min-height: 10;
        border: solid #262626;
        margin: 1 0;
        width: 80;
        background: #1f1f1f;
    }

    #model-options:focus {
        border: solid #757575;
    }

    #model-options > .option-list--option {
        background: #1f1f1f;
        color: #e0e0e0;
    }

    #model-options > .option-list--option-highlighted {
        background: #262626;
        color: #e0e0e0;
    }

    /* Scrollbar styling for model selector */
    #model-options > ScrollBar {
        background: #1f1f1f;
    }

    #model-options > ScrollBar > .scrollbar--thumb {
        background: #757575;
    }

    #model-options > ScrollBar > .scrollbar--thumb:hover {
        background: #757575;
    }

    #model-screen-hint {
        text-align: center;
        color: #757575;
        text-style: bold;
        padding: 1;
        width: 100%;
    }

    #welcome-message {
        text-align: center;
        color: #757575;
        margin-top: 10;
    }

    /* Toast notifications - top right */
    ToastRack {
        dock: top;
        layer: notification;
        offset-y: 1;
        align: right top;
        width: auto;
        margin: 1 1 0 0;
    }

    Toast {
        offset-x: -2;
    }

    /* Header and Footer styling */
    Header {
        background: #1f1f1f;
        color: #e0e0e0;
    }

    Footer {
        background: #1f1f1f;
        color: #757575;
    }

    Footer > .footer--highlight {
        background: #262626;
    }

    Footer > .footer--key {
        background: #262626;
        color: #e0e0e0;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+n", "new_conversation", "New Chat", show=True),
        Binding("ctrl+m", "change_model", "Change Model", show=True),
    ]

    # Notification position
    NOTIFICATION_TIMEOUT = 3

    def __init__(self):
        super().__init__()
        self.config = Config()
        self.client = UnifiedClient(
            ollama_base_url=self.config.ollama_base_url,
            ollama_timeout=self.config.ollama_timeout,
            openai_api_key=self.config.openai_api_key if self.config.has_openai_key else None,
            openai_timeout=self.config.openai_timeout,
        )
        self.storage = ConversationStorage(self.config.conversations_dir)

        # Use last model if available, otherwise use default
        initial_model = self.config.last_model or self.config.default_model
        self.current_conversation = Conversation(model=initial_model)
        self.available_models = []


    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header(show_clock=False)
        with Horizontal(id="main-container"):
            yield Sidebar(self.current_conversation.model)
            with Container(id="chat-container"):
                yield ChatView()
                yield InputBox()
        yield Footer()

    async def on_mount(self) -> None:
        """Handle application mount."""
        self.title = "cmdAI Terminal"
        self.sub_title = "v1.0"

        # Load available models
        self.available_models = await self.client.get_models()
        if not self.available_models:
            # self.notify("Could not load models from API - using fallback models", severity="warning")
            self.available_models = [self.config.default_model]
        # else:
            # self.notify(f"Loaded {len(self.available_models)} models from API", severity="information")

        # Load conversations
        self.refresh_conversation_list()

        # Focus input
        input_box = self.query_one(InputBox)
        input_box.focus_input()

    def refresh_conversation_list(self) -> None:
        """Refresh the conversation list in the sidebar."""
        conversations = self.storage.list_conversations()
        sidebar = self.query_one(Sidebar)
        sidebar.update_conversations(conversations)

    async def on_input_box_send_message(self, message: InputBox.SendMessage) -> None:
        """Handle message send event."""
        # Disable input during processing
        input_box = self.query_one(InputBox)
        input_box.set_enabled(False)

        # Add user message
        user_message = Message(
            role="user",
            content=message.text,
            timestamp=datetime.now(),
        )
        self.current_conversation.add_message(user_message)

        # Display user message
        chat_view = self.query_one(ChatView)
        chat_view.add_message(user_message)

        # Create streaming assistant message
        streaming_widget = chat_view.create_streaming_message()

        # Prepare messages for API
        api_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in self.current_conversation.messages
        ]

        # Stream response
        try:
            async for chunk in self.client.chat_stream(
                self.current_conversation.model,
                api_messages
            ):
                streaming_widget.append_content(chunk)

            # Finalize message
            assistant_message = streaming_widget.finalize(self.current_conversation.model)
            self.current_conversation.add_message(assistant_message)

            # Save conversation
            self.storage.save_conversation(self.current_conversation)
            self.refresh_conversation_list()

        except Exception as e:
            # self.notify(f"Error: {str(e)}", severity="error")
            pass

        finally:
            # Re-enable input
            input_box.set_enabled(True)
            input_box.focus_input()

    def on_sidebar_new_conversation(self, message: Sidebar.NewConversation) -> None:
        """Handle new conversation request."""
        self.action_new_conversation()

    def on_sidebar_select_conversation(self, message: Sidebar.SelectConversation) -> None:
        """Handle conversation selection."""
        self.current_conversation = message.conversation
        chat_view = self.query_one(ChatView)
        chat_view.load_messages(self.current_conversation.messages)

        # Update sidebar model display
        sidebar = self.query_one(Sidebar)
        sidebar.update_model(self.current_conversation.model)

    async def on_sidebar_change_model(self, message: Sidebar.ChangeModel) -> None:
        """Handle model change request."""
        await self.action_change_model()

    def on_sidebar_delete_conversation(self, message: Sidebar.DeleteConversation) -> None:
        """Handle conversation deletion."""
        # Delete from storage
        self.storage.delete_conversation(message.conversation.id)

        # If it's the current conversation, start a new one
        if self.current_conversation.id == message.conversation.id:
            self.action_new_conversation()

        # Refresh the list
        self.refresh_conversation_list()
        # self.notify(f"Deleted conversation: {message.conversation.title}", severity="warning")

    def on_sidebar_clear_all_conversations(self, message: Sidebar.ClearAllConversations) -> None:
        """Handle clearing all conversations."""
        # Get all conversations
        conversations = self.storage.list_conversations()

        # Delete each one
        for conv in conversations:
            self.storage.delete_conversation(conv.id)

        # Start new conversation
        self.action_new_conversation()

        # Refresh list
        self.refresh_conversation_list()
        # self.notify(f"Cleared {len(conversations)} conversations", severity="warning")

    def action_new_conversation(self) -> None:
        """Create a new conversation."""
        self.current_conversation = Conversation(model=self.current_conversation.model)
        chat_view = self.query_one(ChatView)
        chat_view.clear_messages()
        input_box = self.query_one(InputBox)
        input_box.focus_input()
        # self.notify("Started new conversation")

    async def action_change_model(self) -> None:
        """Show model selector."""
        # self.notify(f"Opening model selector with {len(self.available_models)} models...")

        def handle_model_selection(selected_model: str | None) -> None:
            if selected_model:
                self.current_conversation.model = selected_model
                sidebar = self.query_one(Sidebar)
                sidebar.update_model(selected_model)

                # Save the selected model as last used
                self.config.update_last_model(selected_model)

                # self.notify(f"Switched to model: {selected_model}", severity="information")
            else:
                pass
                # self.notify("Model selection cancelled")

        await self.push_screen(
            ModelSelectorScreen(self.available_models, self.current_conversation.model),
            handle_model_selection
        )


def run_app():
    """Run the cmdAI Terminal application."""
    app = CmdAITerminalApp()
    app.run()
