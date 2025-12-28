"""Unified LLM interface wrapper for OpenAI and Gemini providers."""

import asyncio
import base64
import contextlib
import inspect
import time
from collections.abc import Awaitable, Callable

from loguru import logger
from openai import OpenAI

from . import config

app_config = config.get_config()

# AI Provider configuration
AI_PROVIDER = app_config.get(
    "AI", "PROVIDER", fallback="openai"
)  # "openai", "gemini", or "openrouter"

# Model names
OPENAI_MODEL = app_config.get("AI", "OPENAI_MODEL", fallback="gpt-4o-mini")
GEMINI_MODEL = app_config.get("AI", "GEMINI_MODEL", fallback="gemini-2.5-flash")
OPENROUTER_MODEL = app_config.get("AI", "OPENROUTER_MODEL", fallback="openai/gpt-4o-mini")

# Initialize clients
_openai_client: OpenAI | None = None
_gemini_client = None
_openrouter_client: OpenAI | None = None

if AI_PROVIDER == "openai" or app_config.has_option("OPENAI", "API_KEY"):
    try:
        _openai_client = OpenAI(api_key=app_config.get("OPENAI", "API_KEY"))
    except Exception as e:
        logger.warning(f"[ai] Failed to initialize OpenAI client: {e}")

if AI_PROVIDER == "gemini" or app_config.has_option("GEMINI", "API_KEY"):
    try:
        from google import genai

        _gemini_client = genai.Client(api_key=app_config.get("GEMINI", "API_KEY"))
    except Exception as e:
        logger.warning(f"[ai] Failed to initialize Gemini client: {e}")

if AI_PROVIDER == "openrouter" or app_config.has_option("OPENROUTER", "API_KEY"):
    try:
        _openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=app_config.get("OPENROUTER", "API_KEY"),
        )
    except Exception as e:
        logger.warning(f"[ai] Failed to initialize OpenRouter client: {e}")


class LLMResponse:
    """Response from LLM provider."""

    def __init__(self, text: str, provider: str):
        self.text = text
        self.provider = provider


async def _call_callback(callback: Callable[[str], None | Awaitable[None]], text: str):
    """Helper to call callback whether it's sync or async."""
    if inspect.iscoroutinefunction(callback):
        await callback(text)
    else:
        callback(text)


class LLMClient:
    """Unified interface for LLM providers (OpenAI and Gemini)."""

    def __init__(self, provider: str | None = None, model: str | None = None):
        """
        Initialize LLM client.

        Args:
            provider: "openai", "gemini", or "openrouter". If None, uses configured default.
            model: Model name. If None, uses configured default for provider.
        """
        self.provider = provider or AI_PROVIDER
        if self.provider == "openai":
            self.model = model or OPENAI_MODEL
        elif self.provider == "gemini":
            self.model = model or GEMINI_MODEL
        elif self.provider == "openrouter":
            self.model = model or OPENROUTER_MODEL
        else:
            self.model = model or OPENAI_MODEL

        if self.provider == "openai" and _openai_client is None:
            raise ValueError("OpenAI client is not configured.")
        if self.provider == "gemini" and _gemini_client is None:
            raise ValueError("Gemini client is not configured.")
        if self.provider == "openrouter" and _openrouter_client is None:
            raise ValueError("OpenRouter client is not configured.")

    async def generate_streaming(
        self,
        message_text: str,
        image_bytes: bytes | None = None,
        image_mime_type: str | None = None,
        on_chunk: Callable[[str], None | Awaitable[None]] | None = None,
        update_interval: float = 1.0,
    ) -> str:
        """
        Generate streaming response from LLM.

        Args:
            message_text: Text prompt for the LLM.
            image_bytes: Optional image bytes to include.
            image_mime_type: MIME type of the image (e.g., "image/jpeg").
            on_chunk: Optional callback function called with accumulated text on each update.
            update_interval: Minimum seconds between on_chunk callbacks.

        Returns:
            Complete response text.
        """
        if self.provider == "openai":
            return await self._generate_openai_streaming(
                message_text, image_bytes, on_chunk, update_interval
            )
        elif self.provider == "openrouter":
            return await self._generate_openrouter_streaming(
                message_text, image_bytes, on_chunk, update_interval
            )
        elif self.provider == "gemini":
            # Gemini doesn't support streaming in the same way, so we'll use non-streaming
            # and simulate streaming with periodic callbacks
            return await self._generate_gemini_with_simulation(
                message_text, image_bytes, image_mime_type, on_chunk, update_interval
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    async def generate(
        self,
        message_text: str,
        image_bytes: bytes | None = None,
        image_mime_type: str | None = None,
    ) -> LLMResponse:
        """
        Generate non-streaming response from LLM.

        Args:
            message_text: Text prompt for the LLM.
            image_bytes: Optional image bytes to include.
            image_mime_type: MIME type of the image (e.g., "image/jpeg").

        Returns:
            LLMResponse object with text and provider info.
        """
        if self.provider == "openai":
            text = await self._generate_openai(message_text, image_bytes)
            return LLMResponse(text, "openai")
        elif self.provider == "openrouter":
            text = await self._generate_openrouter(message_text, image_bytes)
            return LLMResponse(text, "openrouter")
        elif self.provider == "gemini":
            text = await self._generate_gemini(message_text, image_bytes, image_mime_type)
            return LLMResponse(text, "gemini")
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    async def _generate_openai_streaming(
        self,
        message_text: str,
        image_bytes: bytes | None,
        on_chunk: Callable[[str], None] | None,
        update_interval: float,
    ) -> str:
        """Generate streaming response from OpenAI."""
        # Build content for the message
        content = []

        if image_bytes:
            base64_image = base64.b64encode(bytes(image_bytes)).decode("utf-8")
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                }
            )

        content.append({"type": "text", "text": message_text})

        # Stream response from OpenAI in thread pool to avoid blocking
        def stream_openai():
            stream = _openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": content}],
                stream=True,
            )
            response_text = ""
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    response_text += chunk.choices[0].delta.content
            return response_text

        response_text = await asyncio.to_thread(stream_openai)

        # Call on_chunk callback periodically
        if on_chunk:
            await _call_callback(on_chunk, response_text)

        return response_text

    async def _generate_openai(self, message_text: str, image_bytes: bytes | None) -> str:
        """Generate non-streaming response from OpenAI."""
        # Build content for the message
        content = []

        if image_bytes:
            base64_image = base64.b64encode(bytes(image_bytes)).decode("utf-8")
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                }
            )

        content.append({"type": "text", "text": message_text})

        # Generate response from OpenAI
        response = _openai_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": content}],
            stream=False,
        )

        return response.choices[0].message.content or ""

    async def _generate_openrouter_streaming(
        self,
        message_text: str,
        image_bytes: bytes | None,
        on_chunk: Callable[[str], None] | None,
        update_interval: float,
    ) -> str:
        """Generate streaming response from OpenRouter (OpenAI-compatible API)."""
        # Build content for the message
        content = []

        if image_bytes:
            base64_image = base64.b64encode(bytes(image_bytes)).decode("utf-8")
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                }
            )

        content.append({"type": "text", "text": message_text})

        # Stream response from OpenRouter in thread pool to avoid blocking
        def stream_openrouter():
            stream = _openrouter_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": content}],
                stream=True,
            )
            response_text = ""
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    response_text += chunk.choices[0].delta.content
            return response_text

        response_text = await asyncio.to_thread(stream_openrouter)

        # Call on_chunk callback with final text
        if on_chunk:
            with contextlib.suppress(Exception):
                await _call_callback(on_chunk, response_text)

        return response_text

    async def _generate_openrouter(self, message_text: str, image_bytes: bytes | None) -> str:
        """Generate non-streaming response from OpenRouter (OpenAI-compatible API)."""
        # Build content for the message
        content = []

        if image_bytes:
            base64_image = base64.b64encode(bytes(image_bytes)).decode("utf-8")
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                }
            )

        content.append({"type": "text", "text": message_text})

        # Generate response from OpenRouter
        response = _openrouter_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": content}],
            stream=False,
        )

        return response.choices[0].message.content or ""

    async def _generate_gemini(
        self,
        message_text: str,
        image_bytes: bytes | None,
        image_mime_type: str | None,
    ) -> str:
        """Generate non-streaming response from Gemini."""
        from google.genai import types

        # Build contents for the request
        contents = []

        if image_bytes:
            # Add image as inline data
            contents.append(
                types.Part.from_bytes(
                    data=bytes(image_bytes),
                    mime_type=image_mime_type or "image/jpeg",
                )
            )

        # Add text prompt
        contents.append(message_text)

        # Generate response
        response = _gemini_client.models.generate_content(
            model=self.model,
            contents=contents,
        )

        return response.text

    async def _generate_gemini_with_simulation(
        self,
        message_text: str,
        image_bytes: bytes | None,
        image_mime_type: str | None,
        on_chunk: Callable[[str], None] | None,
        update_interval: float,
    ) -> str:
        """Generate response from Gemini with simulated streaming via callbacks."""
        # Get the full response
        response_text = await self._generate_gemini(message_text, image_bytes, image_mime_type)

        # Simulate streaming by calling on_chunk with progressively more text
        if on_chunk:
            words = response_text.split()
            accumulated = ""
            last_update_time = 0

            for word in words:
                accumulated += word + " "
                current_time = time.time()
                if current_time - last_update_time > update_interval:
                    try:
                        await _call_callback(on_chunk, accumulated.strip())
                        last_update_time = current_time
                    except Exception:
                        pass

            # Final callback with complete text
            with contextlib.suppress(Exception):
                await _call_callback(on_chunk, response_text)

        return response_text


def get_default_client() -> LLMClient:
    """Get default LLM client based on configuration."""
    return LLMClient()


def get_openai_client(model: str | None = None) -> LLMClient:
    """Get OpenAI client with optional custom model."""
    return LLMClient(provider="openai", model=model)


def get_gemini_client(model: str | None = None) -> LLMClient:
    """Get Gemini client with optional custom model."""
    return LLMClient(provider="gemini", model=model)


def get_openrouter_client(model: str | None = None) -> LLMClient:
    """Get OpenRouter client with optional custom model."""
    return LLMClient(provider="openrouter", model=model)
