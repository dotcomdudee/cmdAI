"""Ollama API client with streaming support."""
import httpx
from typing import AsyncIterator, List, Dict, Any
import json


class OllamaClient:
    """Client for interacting with Ollama API."""

    def __init__(self, base_url: str, timeout: int = 60):
        """Initialize the Ollama client."""
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def get_models(self) -> List[str]:
        """Fetch available models from the API."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
                # Extract model names from the response
                models = [model["name"] for model in data.get("models", [])]
                if models:
                    return models
                # If no models in response, return common defaults
                return ["llama2", "llama3", "mistral", "mixtral", "codellama"]
        except Exception as e:
            # Return common model names as fallback
            return ["llama2", "llama3", "mistral", "mixtral", "codellama", "phi3", "gemma"]

    async def chat_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
    ) -> AsyncIterator[str]:
        """
        Stream chat responses from the Ollama API.

        Args:
            model: The model to use for generation
            messages: List of message dicts with 'role' and 'content' keys

        Yields:
            Content chunks as they arrive from the API
        """
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json=payload,
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                chunk = json.loads(line)
                                # Ollama returns content in message.content field
                                if "message" in chunk and "content" in chunk["message"]:
                                    content = chunk["message"]["content"]
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            yield f"\n\n[Error: {str(e)}]"

    async def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
    ) -> str:
        """
        Non-streaming chat request (useful for testing).

        Args:
            model: The model to use for generation
            messages: List of message dicts with 'role' and 'content' keys

        Returns:
            The complete response content
        """
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data.get("message", {}).get("content", "")
        except Exception as e:
            return f"[Error: {str(e)}]"
