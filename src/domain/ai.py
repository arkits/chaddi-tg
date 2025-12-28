"""Unified LLM interface wrapper for OpenAI and Gemini providers."""

import asyncio
import base64
import contextlib
import inspect
import time
from collections.abc import Awaitable, Callable

from loguru import logger

from . import analytics, config

app_config = config.get_config()

# AI Provider configuration
AI_PROVIDER = app_config.get(
    "AI", "PROVIDER", fallback="openai"
)  # "openai", "gemini", or "openrouter"

logger.info(f"[ai] AI_PROVIDER: {AI_PROVIDER}")

# Model names
OPENAI_MODEL = app_config.get("AI", "OPENAI_MODEL", fallback="gpt-5-nano-2025-08-07")
GEMINI_MODEL = app_config.get("AI", "GEMINI_MODEL", fallback="gemini-2.5-flash")
OPENROUTER_MODEL = app_config.get("AI", "OPENROUTER_MODEL", fallback="moonshotai/kimi-k2-0905")

# Always import standard OpenAI first to ensure Sentry can instrument it
from openai import OpenAI as StandardOpenAI  # noqa: E402

# Try to import PostHog's OpenAI wrapper for LLM analytics
try:
    from posthog.ai.openai import OpenAI as PostHogOpenAI

    _posthog_available = True
    _posthog_client = analytics.posthog
    logger.info("[ai] PostHog LLM analytics enabled")
except ImportError:
    PostHogOpenAI = StandardOpenAI  # Fallback to standard OpenAI if PostHog not available
    _posthog_available = False
    _posthog_client = None
    logger.warning("[ai] PostHog AI module not available, using standard OpenAI client")

# Initialize clients with PostHog instrumentation (if available)
_openai_client = None
_gemini_client = None
_openrouter_client = None

if AI_PROVIDER == "openai":
    try:
        if _posthog_available and _posthog_client:
            _openai_client = PostHogOpenAI(
                api_key=app_config.get("OPENAI", "API_KEY"),
                posthog_client=_posthog_client,
            )
            logger.info(
                f"[ai] OpenAI client initialized with model {OPENAI_MODEL} (PostHog enabled)"
            )
        else:
            _openai_client = PostHogOpenAI(api_key=app_config.get("OPENAI", "API_KEY"))
            logger.info(f"[ai] OpenAI client initialized with model {OPENAI_MODEL}")
    except Exception as e:
        logger.warning(f"[ai] Failed to initialize OpenAI client: {e}")

if AI_PROVIDER == "gemini":
    try:
        from google import genai

        _gemini_client = genai.Client(api_key=app_config.get("GEMINI", "API_KEY"))
        logger.info(f"[ai] Gemini client initialized with model {GEMINI_MODEL}")
    except Exception as e:
        logger.warning(f"[ai] Failed to initialize Gemini client: {e}")

if AI_PROVIDER == "openrouter":
    try:
        if _posthog_available and _posthog_client:
            _openrouter_client = PostHogOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=app_config.get("OPENROUTER", "API_KEY"),
                posthog_client=_posthog_client,
            )
            logger.info(
                f"[ai] OpenRouter client initialized with model {OPENROUTER_MODEL} (PostHog enabled)"
            )
        else:
            _openrouter_client = PostHogOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=app_config.get("OPENROUTER", "API_KEY"),
            )
            logger.info(f"[ai] OpenRouter client initialized with model {OPENROUTER_MODEL}")
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
        message_text: str | None = None,
        messages: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
        image_bytes: bytes | None = None,
        image_mime_type: str | None = None,
        on_chunk: Callable[[str], None | Awaitable[None]] | None = None,
        update_interval: float = 1.0,
    ) -> str:
        """
        Generate streaming response from LLM.

        Args:
            message_text: Text prompt for the LLM (deprecated, use messages instead).
            messages: List of message dicts with "role" and "content" keys.
            system_prompt: Optional system prompt to set the assistant's behavior.
            image_bytes: Optional image bytes to include.
            image_mime_type: MIME type of the image (e.g., "image/jpeg").
            on_chunk: Optional callback function called with accumulated text on each update.
            update_interval: Minimum seconds between on_chunk callbacks.

        Returns:
            Complete response text.
        """
        # Convert messages to format expected by providers
        if messages:
            # Use messages list
            if self.provider == "openai":
                return await self._generate_openai_streaming(
                    messages=messages,
                    system_prompt=system_prompt,
                    image_bytes=image_bytes,
                    on_chunk=on_chunk,
                    update_interval=update_interval,
                )
            elif self.provider == "openrouter":
                return await self._generate_openrouter_streaming(
                    messages=messages,
                    system_prompt=system_prompt,
                    image_bytes=image_bytes,
                    on_chunk=on_chunk,
                    update_interval=update_interval,
                )
            elif self.provider == "gemini":
                # Gemini doesn't support streaming in the same way, so we'll use non-streaming
                # and simulate streaming with periodic callbacks
                return await self._generate_gemini_with_simulation(
                    messages=messages,
                    system_prompt=system_prompt,
                    image_bytes=image_bytes,
                    image_mime_type=image_mime_type,
                    on_chunk=on_chunk,
                    update_interval=update_interval,
                )
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        else:
            # Fallback to message_text for backward compatibility
            if not message_text:
                raise ValueError("Either message_text or messages must be provided")
            if self.provider == "openai":
                return await self._generate_openai_streaming(
                    message_text=message_text,
                    system_prompt=system_prompt,
                    image_bytes=image_bytes,
                    on_chunk=on_chunk,
                    update_interval=update_interval,
                )
            elif self.provider == "openrouter":
                return await self._generate_openrouter_streaming(
                    message_text=message_text,
                    system_prompt=system_prompt,
                    image_bytes=image_bytes,
                    on_chunk=on_chunk,
                    update_interval=update_interval,
                )
            elif self.provider == "gemini":
                # Gemini doesn't support streaming in the same way, so we'll use non-streaming
                # and simulate streaming with periodic callbacks
                return await self._generate_gemini_with_simulation(
                    message_text=message_text,
                    system_prompt=system_prompt,
                    image_bytes=image_bytes,
                    image_mime_type=image_mime_type,
                    on_chunk=on_chunk,
                    update_interval=update_interval,
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
        message_text: str | None = None,
        messages: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
        image_bytes: bytes | None = None,
        on_chunk: Callable[[str], None] | None = None,
        update_interval: float = 1.0,
    ) -> str:
        """Generate streaming response from OpenAI."""
        # Build messages list
        if messages:
            # Use provided messages list, but handle images in the last user message
            formatted_messages = []

            # Add system prompt if provided (must be first)
            if system_prompt:
                formatted_messages.append({"role": "system", "content": system_prompt})

            for msg in messages:
                if msg["role"] == "user" and image_bytes and msg == messages[-1]:
                    # Add image to the last user message
                    content = []
                    base64_image = base64.b64encode(bytes(image_bytes)).decode("utf-8")
                    content.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        }
                    )
                    content.append({"type": "text", "text": msg["content"]})
                    formatted_messages.append({"role": "user", "content": content})
                else:
                    formatted_messages.append(msg)
        else:
            # Build content for single message
            if not message_text:
                raise ValueError("Either message_text or messages must be provided")
            formatted_messages = []

            # Add system prompt if provided (must be first)
            if system_prompt:
                formatted_messages.append({"role": "system", "content": system_prompt})

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
            formatted_messages.append({"role": "user", "content": content})

        # Stream response from OpenAI in thread pool to avoid blocking
        def stream_openai():
            stream = _openai_client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                stream=True,
                max_completion_tokens=2000,
            )
            response_text = ""
            for chunk in stream:
                # Check if choices exist and have at least one element
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content is not None:
                        response_text += delta.content
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
            max_completion_tokens=2000,
        )

        return response.choices[0].message.content or ""

    async def _generate_openrouter_streaming(
        self,
        message_text: str | None = None,
        messages: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
        image_bytes: bytes | None = None,
        on_chunk: Callable[[str], None] | None = None,
        update_interval: float = 1.0,
    ) -> str:
        """Generate streaming response from OpenRouter (OpenAI-compatible API)."""
        # Build messages list (same logic as OpenAI)
        if messages:
            formatted_messages = []

            # Add system prompt if provided (must be first)
            if system_prompt:
                formatted_messages.append({"role": "system", "content": system_prompt})

            for msg in messages:
                if msg["role"] == "user" and image_bytes and msg == messages[-1]:
                    content = []
                    base64_image = base64.b64encode(bytes(image_bytes)).decode("utf-8")
                    content.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        }
                    )
                    content.append({"type": "text", "text": msg["content"]})
                    formatted_messages.append({"role": "user", "content": content})
                else:
                    formatted_messages.append(msg)
        else:
            if not message_text:
                raise ValueError("Either message_text or messages must be provided")
            formatted_messages = []

            # Add system prompt if provided (must be first)
            if system_prompt:
                formatted_messages.append({"role": "system", "content": system_prompt})

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
            formatted_messages.append({"role": "user", "content": content})

        # Stream response from OpenRouter in thread pool to avoid blocking
        def stream_openrouter():
            stream = _openrouter_client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                stream=True,
                max_completion_tokens=2000,
            )
            response_text = ""
            for chunk in stream:
                # Check if choices exist and have at least one element
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content is not None:
                        response_text += delta.content
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
            max_completion_tokens=2000,
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
        message_text: str | None = None,
        messages: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
        image_bytes: bytes | None = None,
        image_mime_type: str | None = None,
        on_chunk: Callable[[str], None] | None = None,
        update_interval: float = 1.0,
    ) -> str:
        """Generate response from Gemini with simulated streaming via callbacks."""
        # Convert messages to text format for Gemini (Gemini doesn't support structured messages)
        if messages:
            # Convert messages list to a single text prompt
            conversation_text = ""

            # Add system prompt if provided
            if system_prompt:
                conversation_text += f"System: {system_prompt}\n\n"

            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "system":
                    # System messages already handled above
                    continue
                elif role == "user":
                    conversation_text += f"User: {content}\n\n"
                elif role == "assistant":
                    conversation_text += f"Assistant: {content}\n\n"
            message_text = conversation_text.strip()
        elif not message_text:
            raise ValueError("Either message_text or messages must be provided")
        else:
            # Add system prompt to single message if provided
            if system_prompt:
                message_text = f"System: {system_prompt}\n\n{message_text}"

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
