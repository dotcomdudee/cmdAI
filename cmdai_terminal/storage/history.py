"""Conversation history storage."""
import json
from pathlib import Path
from typing import List

from ..models.conversation import Conversation


class ConversationStorage:
    """Manages conversation persistence."""

    def __init__(self, storage_dir: Path):
        """Initialize storage manager."""
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_conversation(self, conversation: Conversation) -> None:
        """Save a conversation to disk."""
        file_path = self.storage_dir / f"{conversation.id}.json"
        with open(file_path, "w") as f:
            json.dump(conversation.to_dict(), f, indent=2)

    def load_conversation(self, conversation_id: str) -> Conversation | None:
        """Load a conversation from disk."""
        file_path = self.storage_dir / f"{conversation_id}.json"
        if not file_path.exists():
            return None

        with open(file_path) as f:
            data = json.load(f)
        return Conversation.from_dict(data)

    def list_conversations(self) -> List[Conversation]:
        """List all saved conversations."""
        conversations = []
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path) as f:
                    data = json.load(f)
                conversations.append(Conversation.from_dict(data))
            except Exception:
                # Skip corrupted files
                continue

        # Sort by updated_at, most recent first
        conversations.sort(key=lambda c: c.updated_at, reverse=True)
        return conversations

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        file_path = self.storage_dir / f"{conversation_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False
