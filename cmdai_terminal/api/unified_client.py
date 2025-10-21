"""Unified API client that supports both Ollama and OpenAI."""
from typing import AsyncIterator, List, Dict, Any
from .ollama import OllamaClient
from .openai_client import OpenAIClient


class UnifiedClient:
    """
    Unified client that routes requests to Ollama or OpenAI based on model name.

    OpenAI models are prefixed with 'openai/' (e.g., 'openai/gpt-4o')
    Ollama models have no prefix (e.g., 'llama2')
    """

    def __init__(
        self,
        ollama_base_url: str,
        ollama_timeout: int,
        openai_api_key: str | None = None,
        openai_timeout: int = 60,
    ):
        """Initialize the unified client."""
        self.ollama_client = OllamaClient(ollama_base_url, ollama_timeout)
        self.openai_client = None

        if openai_api_key:
            self.openai_client = OpenAIClient(openai_api_key, openai_timeout)

    @staticmethod
    def is_openai_model(model: str) -> bool:
        """Check if a model name refers to an OpenAI model."""
        return model.startswith("openai/")

    @staticmethod
    def strip_provider_prefix(model: str) -> str:
        """Remove the provider prefix from a model name."""
        if model.startswith("openai/"):
            return model[7:]  # Remove "openai/" prefix
        return model

    @staticmethod
    def add_provider_prefix(model: str, provider: str) -> str:
        """Add provider prefix to a model name."""
        if provider == "openai":
            return f"openai/{model}"
        return model

    async def get_models(self) -> List[str]:
        """
        Fetch available models from both Ollama and OpenAI.

        Returns a combined list with OpenAI models prefixed with 'openai/'
        """
        models = []

        # Get Ollama models
        try:
            ollama_models = await self.ollama_client.get_models()
            models.extend(ollama_models)
        except Exception:
            pass

        # Get OpenAI models if API key is configured
        if self.openai_client:
            try:
                openai_models = await self.openai_client.get_models()
                # Add openai/ prefix to distinguish them
                prefixed_openai_models = [
                    self.add_provider_prefix(m, "openai")
                    for m in openai_models
                ]
                models.extend(prefixed_openai_models)
            except Exception:
                pass

        # Return models or fallback
        return models if models else ["llama2"]

    async def chat_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
    ) -> AsyncIterator[str]:
        """
        Stream chat responses from the appropriate provider.

        Args:
            model: The model to use (with or without provider prefix)
            messages: List of message dicts with 'role' and 'content' keys

        Yields:
            Content chunks as they arrive from the API
        """
        if self.is_openai_model(model):
            # Route to OpenAI
            if not self.openai_client:
                yield "[Error: OpenAI API key not configured]"
                return

            clean_model = self.strip_provider_prefix(model)
            async for chunk in self.openai_client.chat_stream(clean_model, messages):
                yield chunk
        else:
            # Route to Ollama
            async for chunk in self.ollama_client.chat_stream(model, messages):
                yield chunk

    async def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
    ) -> str:
        """
        Non-streaming chat request to the appropriate provider.

        Args:
            model: The model to use (with or without provider prefix)
            messages: List of message dicts with 'role' and 'content' keys

        Returns:
            The complete response content
        """
        if self.is_openai_model(model):
            # Route to OpenAI
            if not self.openai_client:
                return "[Error: OpenAI API key not configured]"

            clean_model = self.strip_provider_prefix(model)
            return await self.openai_client.chat(clean_model, messages)
        else:
            # Route to Ollama
            return await self.ollama_client.chat(model, messages)
