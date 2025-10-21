"""Configuration management."""
import os
from pathlib import Path
from typing import Any
import yaml


class Config:
    """Application configuration manager."""

    def __init__(self, config_path: str | None = None):
        """Initialize configuration."""
        if config_path is None:
            # Try current directory first, then user home
            if Path("config.yaml").exists():
                config_path = "config.yaml"
            else:
                config_path = str(Path.home() / ".cmdai-terminal" / "config.yaml")

        self.config_path = Path(config_path)
        self.data = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from file."""
        if not self.config_path.exists():
            # Return default config
            return {
                "api": {
                    "ollama": {
                        "base_url": "http://localhost:11434",
                        "timeout": 60,
                    },
                    "openai": {
                        "api_key": None,
                        "timeout": 60,
                    },
                },
                "ui": {
                    "theme": "dark",
                    "sidebar_width": 35,
                    "message_padding": 2,
                },
                "storage": {
                    "conversations_dir": "~/.cmdai-terminal/conversations",
                },
                "default_model": "llama2",
            }

        with open(self.config_path) as f:
            return yaml.safe_load(f)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        keys = key.split(".")
        value = self.data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    @property
    def ollama_base_url(self) -> str:
        """Get Ollama API base URL."""
        return self.get("api.ollama.base_url", "http://localhost:11434")

    @property
    def ollama_timeout(self) -> int:
        """Get Ollama API timeout."""
        return self.get("api.ollama.timeout", 60)

    @property
    def openai_api_key(self) -> str | None:
        """Get OpenAI API key."""
        return self.get("api.openai.api_key", None)

    @property
    def openai_timeout(self) -> int:
        """Get OpenAI API timeout."""
        return self.get("api.openai.timeout", 60)

    @property
    def has_openai_key(self) -> bool:
        """Check if OpenAI API key is configured."""
        key = self.openai_api_key
        return key is not None and key != "" and key.lower() != "null"

    @property
    def conversations_dir(self) -> Path:
        """Get conversations directory path."""
        path = self.get("storage.conversations_dir", "~/.cmdai-terminal/conversations")
        return Path(os.path.expanduser(path))

    @property
    def default_model(self) -> str:
        """Get default model."""
        return self.get("default_model", "llama2")

    @property
    def sidebar_width(self) -> int:
        """Get sidebar width."""
        return self.get("ui.sidebar_width", 35)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation."""
        keys = key.split(".")
        data = self.data

        # Navigate to the parent dict
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]

        # Set the value
        data[keys[-1]] = value

    def save(self) -> None:
        """Save configuration to file."""
        # Create directory if it doesn't exist
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_path, "w") as f:
            yaml.safe_dump(self.data, f, default_flow_style=False, sort_keys=False)

    def update_last_model(self, model: str) -> None:
        """Update the last used model and save config."""
        self.set("last_model", model)
        self.save()

    @property
    def last_model(self) -> str | None:
        """Get last used model, or None if not set."""
        return self.get("last_model", None)
