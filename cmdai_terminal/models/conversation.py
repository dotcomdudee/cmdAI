"""Conversation data model."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List
import uuid

from .message import Message


@dataclass
class Conversation:
    """Represents a conversation with messages."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "New Conversation"
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    model: str = "llama2"

    def add_message(self, message: Message) -> None:
        """Add a message to the conversation."""
        self.messages.append(message)
        self.updated_at = datetime.now()

        # Auto-generate title from first user message
        if len(self.messages) == 1 and message.role == "user" and self.title == "New Conversation":
            self.title = message.content[:50] + ("..." if len(message.content) > 50 else "")

    def to_dict(self) -> dict:
        """Convert conversation to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "messages": [msg.to_dict() for msg in self.messages],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "model": self.model,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Conversation":
        """Create conversation from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            messages=[Message.from_dict(msg) for msg in data["messages"]],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            model=data.get("model", "llama2"),
        )
