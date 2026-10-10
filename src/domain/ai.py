"""Unified LLM interface wrapper for OpenAI and Gemini providers."""

import asyncio
import base64
import contextlib
import inspect
import json
import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

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
OPENROUTER_MODEL = app_config.get("AI", "OPENROUTER_MODEL", fallback="moonshotai/kimi-k2.5")
# Optional fallback models for OpenRouter (comma-separated list)
OPENROUTER_FALLBACK_MODELS = app_config.get("AI", "OPENROUTER_FALLBACK_MODELS", fallback="")
# Enable web search server tool for OpenRouter requests
OPENROUTER_WEB_SEARCH = app_config.getboolean("AI", "OPENROUTER_WEB_SEARCH", fallback=True)
# Parse fallback models into a list if configured
_openrouter_fallback_models = (
    [m.strip() for m in OPENROUTER_FALLBACK_MODELS.split(",") if m.strip()]
    if OPENROUTER_FALLBACK_MODELS
    else None
)

# Always import standard OpenAI first to ensure Sentry can instrument it
from openai import OpenAI as StandardOpenAI  # noqa: E402

# Try to import PostHog's OpenAI wrapper for LLM analytics
try:
    from posthog.ai.gemini import Client as PostHogGemini
    from posthog.ai.openai import OpenAI as PostHogOpenAI

    _posthog_available = True
    _posthog_client = analytics.posthog
    _posthog_wrappers: tuple[type, ...] = (PostHogOpenAI, PostHogGemini)
    logger.info("[ai] PostHog LLM analytics enabled")
except ImportError:
    PostHogOpenAI = StandardOpenAI  # Fallback to standard OpenAI if PostHog not available
    PostHogGemini = None
    _posthog_available = False
    _posthog_client = None
    _posthog_wrappers = ()
    logger.warning("[ai] PostHog AI module not available, using standard OpenAI client")

# Initialize clients with PostHog instrumentation (if available)
_openai_client = None
_gemini_client = None
_openrouter_client = None

try:
    _openai_client = PostHogOpenAI(
        api_key=app_config.get("OPENAI", "API_KEY"), posthog_client=_posthog_client
    )
    logger.info(f"[ai] OpenAI client initialized with model {OPENAI_MODEL}")
except Exception as e:
    logger.debug(f"[ai] Failed to initialize OpenAI client: {e}")
    try:
        _openai_client = StandardOpenAI(api_key=app_config.get("OPENAI", "API_KEY"))
        logger.info(f"[ai] OpenAI client initialized (standard) with model {OPENAI_MODEL}")
    except Exception as e2:
        logger.debug(f"[ai] Failed to initialize OpenAI client (standard): {e2}")

try:
    from google import genai

    if PostHogGemini is not None:
        _gemini_client = PostHogGemini(
            api_key=app_config.get("GEMINI", "API_KEY"), posthog_client=_posthog_client
        )
    else:
        _gemini_client = genai.Client(api_key=app_config.get("GEMINI", "API_KEY"))
    logger.info(f"[ai] Gemini client initialized with model {GEMINI_MODEL}")
except Exception as e:
    logger.debug(f"[ai] Failed to initialize Gemini client: {e}")

try:
    _openrouter_client = PostHogOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=app_config.get("OPENROUTER", "API_KEY"),
        posthog_client=_posthog_client,
    )
    logger.info(f"[ai] OpenRouter client initialized with model {OPENROUTER_MODEL}")
except Exception as e:
    logger.debug(f"[ai] Failed to initialize OpenRouter client: {e}")
    try:
        _openrouter_client = StandardOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=app_config.get("OPENROUTER", "API_KEY"),
        )
        logger.info(f"[ai] OpenRouter client initialized (standard) with model {OPENROUTER_MODEL}")
    except Exception as e2:
        logger.debug(f"[ai] Failed to initialize OpenRouter client (standard): {e2}")


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


# Hard cap on model <-> tool round trips per request, so a model that keeps
# calling tools can't loop forever
MAX_TOOL_ROUNDS = 4


@dataclass
class LLMTool:
    """A function the model can call while generating a response."""

    name: str
    description: str
    # JSON schema for the function's arguments
    parameters: dict
    # Called with the parsed arguments as kwargs; returns the result as text
    handler: Callable[..., str | Awaitable[str]]

    def to_openai(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


async def _run_tool(tool: LLMTool, raw_arguments: str) -> str:
    """Run a tool call, returning errors as text so the model can recover."""
    try:
        arguments = json.loads(raw_arguments) if raw_arguments else {}
        if not isinstance(arguments, dict):
            raise ValueError("arguments must be a JSON object")
    except Exception as e:
        logger.warning(f"[ai] Bad arguments for tool {tool.name}: {raw_arguments!r} - {e}")
        return f"Error: could not parse arguments - {e}"

    try:
        logger.info(f"[ai] Running tool {tool.name} with {arguments}")
        result = tool.handler(**arguments)
        if inspect.isawaitable(result):
            result = await result
        return str(result)
    except Exception as e:
        logger.warning(f"[ai] Tool {tool.name} failed: {e}")
        return f"Error: {e}"


def _build_openai_messages(
    message_text: str | None,
    messages: list[dict[str, str]] | None,
    system_prompt: str | None,
    image_bytes: bytes | None,
) -> list[dict]:
    """Build an OpenAI-style messages list, attaching the image to the last user message."""
    if not messages:
        if not message_text:
            raise ValueError("Either message_text or messages must be provided")
        messages = [{"role": "user", "content": message_text}]

    formatted_messages = []

    # Add system prompt if provided (must be first)
    if system_prompt:
        formatted_messages.append({"role": "system", "content": system_prompt})

    last_index = len(messages) - 1
    for i, msg in enumerate(messages):
        if i == last_index and msg["role"] == "user" and image_bytes:
            base64_image = base64.b64encode(bytes(image_bytes)).decode("utf-8")
            content = [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                },
                {"type": "text", "text": msg["content"]},
            ]
            formatted_messages.append({"role": "user", "content": content})
        else:
            formatted_messages.append(msg)

    return formatted_messages


class LLMClient:
    """Unified interface for LLM providers (OpenAI and Gemini)."""

    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
        models: list[str] | None = None,
        distinct_id: str | None = None,
        properties: dict | None = None,
        _client=None,
    ):
        """
        Initialize LLM client.

        Args:
            provider: "openai", "gemini", or "openrouter". If None, uses configured default.
            model: Model name. If None, uses configured default for provider.
            models: List of fallback model IDs for OpenRouter. If None, uses configured default.
                    Only used when provider is "openrouter".
            distinct_id: Telegram user ID the generations are attributed to in PostHog.
            properties: Extra properties attached to the PostHog $ai_generation events.
            _client: Optional client override (for internal use).
        """
        self.provider = provider or AI_PROVIDER
        self.distinct_id = distinct_id
        self.properties = properties or {}
        self._client_override = _client
        if self.provider == "openai":
            self.model = model or OPENAI_MODEL
            self.models = None  # Fallback models not supported for OpenAI
        elif self.provider == "gemini":
            self.model = model or GEMINI_MODEL
            self.models = None  # Fallback models not supported for Gemini
        elif self.provider == "openrouter":
            self.model = model or OPENROUTER_MODEL
            # Use provided models, or fall back to configured defaults
            self.models = models if models is not None else _openrouter_fallback_models
        else:
            self.model = model or OPENAI_MODEL
            self.models = None

        if self._client_override is None:
            if self.provider == "openai" and _openai_client is None:
                raise ValueError("OpenAI client is not configured.")
            if self.provider == "gemini" and _gemini_client is None:
                raise ValueError("Gemini client is not configured.")
            if self.provider == "openrouter" and _openrouter_client is None:
                raise ValueError("OpenRouter client is not configured.")

    def _posthog_kwargs(self, client) -> dict:
        """
        PostHog tracking kwargs for a request, when the client is PostHog-wrapped.

        Each call starts a new trace, so every model <-> tool round of one request
        shows up as a single trace in PostHog AI observability.
        """
        if not _posthog_wrappers or not isinstance(client, _posthog_wrappers):
            return {}
        return {
            "posthog_distinct_id": self.distinct_id,
            "posthog_trace_id": str(uuid.uuid4()),
            "posthog_properties": {"provider": self.provider, **self.properties},
        }

    @property
    def has_web_search(self) -> bool:
        """Whether responses from this client can use real-time web search."""
        return self.provider == "openrouter" and OPENROUTER_WEB_SEARCH

    async def generate_streaming(
        self,
        message_text: str | None = None,
        messages: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
        image_bytes: bytes | None = None,
        image_mime_type: str | None = None,
        on_chunk: Callable[[str], None | Awaitable[None]] | None = None,
        update_interval: float = 1.0,
        tools: list[LLMTool] | None = None,
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
            tools: Optional functions the model may call. Supported for the OpenAI and
                OpenRouter providers; ignored for Gemini.

        Returns:
            Complete response text.
        """
        if not messages and not message_text:
            raise ValueError("Either message_text or messages must be provided")

        if self.provider == "openai":
            return await self._generate_openai_streaming(
                message_text=message_text,
                messages=messages,
                system_prompt=system_prompt,
                image_bytes=image_bytes,
                on_chunk=on_chunk,
                update_interval=update_interval,
                tools=tools,
            )
        elif self.provider == "openrouter":
            return await self._generate_openrouter_streaming(
                message_text=message_text,
                messages=messages,
                system_prompt=system_prompt,
                image_bytes=image_bytes,
                on_chunk=on_chunk,
                update_interval=update_interval,
                tools=tools,
            )
        elif self.provider == "gemini":
            if tools:
                logger.debug("[ai] Tools are not supported for Gemini, ignoring")
            # Gemini doesn't support streaming in the same way, so we'll use non-streaming
            # and simulate streaming with periodic callbacks
            return await self._generate_gemini_with_simulation(
                message_text=message_text,
                messages=messages,
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
        on_chunk: Callable[[str], None | Awaitable[None]] | None = None,
        update_interval: float = 1.0,
        tools: list[LLMTool] | None = None,
    ) -> str:
        """Generate streaming response from OpenAI."""
        client = self._client_override or _openai_client
        assert client is not None, "OpenAI client not configured"
        return await self._stream_chat_completion(
            client=client,
            formatted_messages=_build_openai_messages(
                message_text, messages, system_prompt, image_bytes
            ),
            extra_kwargs=self._posthog_kwargs(client),
            server_tools=[],
            tools=tools,
            on_chunk=on_chunk,
            update_interval=update_interval,
        )

    async def _stream_chat_completion(
        self,
        client,
        formatted_messages: list[dict],
        extra_kwargs: dict,
        server_tools: list[dict],
        tools: list[LLMTool] | None,
        on_chunk: Callable[[str], None | Awaitable[None]] | None,
        update_interval: float,
    ) -> str:
        """
        Stream a chat completion from an OpenAI-compatible API, running any tool
        calls the model makes and feeding the results back until it answers.

        The blocking SDK stream is consumed in a worker thread. on_chunk is invoked
        on the event loop at most once per update_interval while text streams in,
        and once more with the final text.
        """
        loop = asyncio.get_running_loop()
        tool_map = {t.name: t for t in tools or []}
        conversation = list(formatted_messages)

        def emit(text: str):
            future = asyncio.run_coroutine_threadsafe(_call_callback(on_chunk, text), loop)
            # Wait so edits land in order and none arrive after the final one
            with contextlib.suppress(Exception):
                future.result(timeout=10)

        def consume(create_kwargs: dict) -> tuple[str, dict[int, dict[str, str]]]:
            text = ""
            tool_calls: dict[int, dict[str, str]] = {}
            last_emit = 0.0
            for chunk in client.chat.completions.create(**create_kwargs):
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if delta is None:
                    continue
                if delta.content is not None:
                    text += delta.content
                    if on_chunk and time.monotonic() - last_emit >= update_interval:
                        last_emit = time.monotonic()
                        emit(text)
                for tool_call in getattr(delta, "tool_calls", None) or []:
                    index = tool_call.index if isinstance(tool_call.index, int) else 0
                    entry = tool_calls.setdefault(index, {"id": "", "name": "", "arguments": ""})
                    if isinstance(tool_call.id, str):
                        entry["id"] = tool_call.id
                    function = tool_call.function
                    if function is not None:
                        if isinstance(function.name, str):
                            entry["name"] += function.name
                        if isinstance(function.arguments, str):
                            entry["arguments"] += function.arguments
            return text, tool_calls

        response_text = ""
        for round_num in range(MAX_TOOL_ROUNDS + 1):
            create_kwargs = {
                "model": self.model,
                "messages": conversation,
                "stream": True,
                "max_completion_tokens": 2000,
                **extra_kwargs,
            }
            all_tools = server_tools + [t.to_openai() for t in tools or []]
            if all_tools:
                create_kwargs["tools"] = all_tools
            if tool_map and round_num == MAX_TOOL_ROUNDS:
                # Out of tool rounds - make the model answer with what it has
                create_kwargs["tool_choice"] = "none"

            response_text, tool_calls = await asyncio.to_thread(consume, create_kwargs)

            # Server-side tools (eg. openrouter:web_search) are resolved by the
            # provider, so only our own function tools need a round trip
            own_calls = [c for c in tool_calls.values() if c["name"] in tool_map]
            if not own_calls:
                break

            conversation.append(
                {
                    "role": "assistant",
                    "content": response_text or None,
                    "tool_calls": [
                        {
                            "id": c["id"],
                            "type": "function",
                            "function": {"name": c["name"], "arguments": c["arguments"] or "{}"},
                        }
                        for c in own_calls
                    ],
                }
            )
            for call in own_calls:
                result = await _run_tool(tool_map[call["name"]], call["arguments"])
                conversation.append({"role": "tool", "tool_call_id": call["id"], "content": result})

        if on_chunk:
            with contextlib.suppress(Exception):
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
        client = self._client_override or _openai_client
        assert client is not None, "OpenAI client not configured"
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": content}],
            stream=False,
            max_completion_tokens=2000,
            **self._posthog_kwargs(client),
        )

        return response.choices[0].message.content or ""

    async def _generate_openrouter_streaming(
        self,
        message_text: str | None = None,
        messages: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
        image_bytes: bytes | None = None,
        on_chunk: Callable[[str], None | Awaitable[None]] | None = None,
        update_interval: float = 1.0,
        tools: list[LLMTool] | None = None,
    ) -> str:
        """Generate streaming response from OpenRouter (OpenAI-compatible API)."""
        client = self._client_override or _openrouter_client
        assert client is not None, "OpenRouter client not configured"

        # Fallback models are passed through extra_body when configured
        extra_kwargs = self._posthog_kwargs(client)
        if self.models:
            extra_kwargs["extra_body"] = {"models": self.models}

        server_tools = []
        if OPENROUTER_WEB_SEARCH:
            server_tools.append({"type": "openrouter:web_search"})
        server_tools.append({"type": "openrouter:datetime"})

        return await self._stream_chat_completion(
            client=client,
            formatted_messages=_build_openai_messages(
                message_text, messages, system_prompt, image_bytes
            ),
            extra_kwargs=extra_kwargs,
            server_tools=server_tools,
            tools=tools,
            on_chunk=on_chunk,
            update_interval=update_interval,
        )

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

        # Build extra_body with models if fallback models are configured
        extra_body = {}
        if self.models:
            extra_body["models"] = self.models

        # Generate response from OpenRouter
        create_kwargs = {
            "model": self.model,
            "messages": [{"role": "user", "content": content}],
            "stream": False,
            "max_completion_tokens": 2000,
        }
        if extra_body:
            create_kwargs["extra_body"] = extra_body
        tools = []
        if OPENROUTER_WEB_SEARCH:
            tools.append({"type": "openrouter:web_search"})
        tools.append({"type": "openrouter:datetime"})
        create_kwargs["tools"] = tools

        client = self._client_override or _openrouter_client
        assert client is not None, "OpenRouter client not configured"
        response = client.chat.completions.create(**create_kwargs, **self._posthog_kwargs(client))

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
        client = self._client_override or _gemini_client
        assert client is not None, "Gemini client not configured"
        response = client.models.generate_content(
            model=self.model,
            contents=contents,
            **self._posthog_kwargs(client),
        )

        return response.text or ""

    async def _generate_gemini_with_simulation(
        self,
        message_text: str | None = None,
        messages: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
        image_bytes: bytes | None = None,
        image_mime_type: str | None = None,
        on_chunk: Callable[[str], None | Awaitable[None]] | None = None,
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


def get_default_client(distinct_id: str | None = None, properties: dict | None = None) -> LLMClient:
    """Get default LLM client based on configuration."""
    return LLMClient(distinct_id=distinct_id, properties=properties)


def get_openai_client(
    model: str | None = None, distinct_id: str | None = None, properties: dict | None = None
) -> LLMClient:
    """Get OpenAI client with optional custom model."""
    return LLMClient(provider="openai", model=model, distinct_id=distinct_id, properties=properties)


def get_gemini_client(
    model: str | None = None, distinct_id: str | None = None, properties: dict | None = None
) -> LLMClient:
    """Get Gemini client with optional custom model."""
    return LLMClient(provider="gemini", model=model, distinct_id=distinct_id, properties=properties)


def get_openrouter_client(
    model: str | None = None,
    models: list[str] | None = None,
    distinct_id: str | None = None,
    properties: dict | None = None,
) -> LLMClient:
    """
    Get OpenRouter client with optional custom model and fallback models.

    Args:
        model: Primary model name. If None, uses configured default.
        models: List of fallback model IDs. If None, uses configured default.
        distinct_id: Telegram user ID the generations are attributed to in PostHog.
        properties: Extra properties attached to the PostHog $ai_generation events.

    Returns:
        LLMClient configured for OpenRouter.
    """
    return LLMClient(
        provider="openrouter",
        model=model,
        models=models,
        distinct_id=distinct_id,
        properties=properties,
    )


def get_chatgpt_client(model: str | None = None) -> LLMClient:
    """
    Get ChatGPT (OpenAI) client - always uses OpenAI regardless of configured provider.

    Args:
        model: Model name. If None, uses configured OpenAI default model.

    Returns:
        LLMClient configured for OpenAI.
    """
    try:
        client = PostHogOpenAI(
            api_key=app_config.get("OPENAI", "API_KEY"), posthog_client=_posthog_client
        )
    except Exception:
        client = StandardOpenAI(api_key=app_config.get("OPENAI", "API_KEY"))
    return LLMClient(provider="openai", model=model or OPENAI_MODEL, _client=client)
