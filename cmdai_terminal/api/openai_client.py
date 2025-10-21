"""OpenAI API client with streaming support."""
import httpx
from typing import AsyncIterator, List, Dict, Any
import json


class OpenAIClient:
    """Client for interacting with OpenAI API."""

    def __init__(self, api_key: str, timeout: int = 60):
        """Initialize the OpenAI client."""
        self.api_key = api_key
        self.timeout = timeout
        self.base_url = "https://api.openai.com/v1"

    async def get_models(self) -> List[str]:
        """Fetch available models from the OpenAI API."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                data = response.json()

                # Extract all model IDs
                all_models = [model["id"] for model in data.get("data", [])]

                # Sort alphabetically for consistency
                all_models.sort()

                if all_models:
                    return all_models

                # Fallback to common models
                return ["gpt-4o", "gpt-4-turbo-preview", "gpt-3.5-turbo"]

        except Exception as e:
            # Return common model names as fallback
            return ["gpt-4o", "gpt-4-turbo-preview", "gpt-3.5-turbo"]

    async def chat_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
    ) -> AsyncIterator[str]:
        """
        Stream chat responses from the OpenAI API.

        Args:
            model: The model to use for generation
            messages: List of message dicts with 'role' and 'content' keys

        Yields:
            Content chunks as they arrive from the API
        """
        # Convert messages to OpenAI format (remove timestamp and model fields)
        openai_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]

        payload = {
            "model": model,
            "messages": openai_messages,
            "stream": True,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if line.strip():
                            # OpenAI uses SSE format: "data: {json}"
                            if line.startswith("data: "):
                                data_str = line[6:]  # Remove "data: " prefix

                                # Skip the [DONE] message
                                if data_str.strip() == "[DONE]":
                                    continue

                                try:
                                    chunk = json.loads(data_str)
                                    # OpenAI returns content in choices[0].delta.content
                                    if "choices" in chunk and len(chunk["choices"]) > 0:
                                        delta = chunk["choices"][0].get("delta", {})
                                        content = delta.get("content")
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
        # Convert messages to OpenAI format
        openai_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]

        payload = {
            "model": model,
            "messages": openai_messages,
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()
                data = response.json()

                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0].get("message", {}).get("content", "")
                return ""
        except Exception as e:
            return f"[Error: {str(e)}]"
