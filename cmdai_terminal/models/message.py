"""Message data model."""
from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass
class Message:
    """Represents a single message in a conversation."""

    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime
    model: str | None = None

    def to_dict(self) -> dict:
        """Convert message to dictionary for serialization."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "model": self.model,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        """Create message from dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            model=data.get("model"),
        )
