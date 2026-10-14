"""Unified LLM interface wrapper for OpenRouter and OpenAI."""

import asyncio
import base64
import contextlib
import inspect
import json
import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

import requests
from loguru import logger

from . import analytics, config

app_config = config.get_config()

SUPPORTED_PROVIDERS = ("openrouter", "openai")

# AI Provider configuration - "openrouter" (preferred) or "openai"
AI_PROVIDER = app_config.get("AI", "PROVIDER", fallback="openrouter")
if AI_PROVIDER not in SUPPORTED_PROVIDERS:
    logger.warning(f"[ai] Unsupported AI_PROVIDER={AI_PROVIDER!r}, using openrouter")
    AI_PROVIDER = "openrouter"

logger.info(f"[ai] AI_PROVIDER: {AI_PROVIDER}")

# Model names
OPENAI_MODEL = app_config.get("AI", "OPENAI_MODEL", fallback="gpt-5-nano-2025-08-07")
OPENROUTER_MODEL = app_config.get("AI", "OPENROUTER_MODEL", fallback="moonshotai/kimi-k2.5")
# Optional fallback models for OpenRouter (comma-separated list)
OPENROUTER_FALLBACK_MODELS = app_config.get("AI", "OPENROUTER_FALLBACK_MODELS", fallback="")
# Enable web search server tool for OpenRouter requests
OPENROUTER_WEB_SEARCH = app_config.getboolean("AI", "OPENROUTER_WEB_SEARCH", fallback=True)
# How OpenRouter reads attached PDFs: "pdf-text" (free), "mistral-ocr" (paid, handles
# scans) or "native" (the model's own file support, where it has one)
OPENROUTER_PDF_ENGINE = app_config.get("AI", "OPENROUTER_PDF_ENGINE", fallback="pdf-text")
# Model used to generate images
OPENROUTER_IMAGE_MODEL = app_config.get(
    "AI", "OPENROUTER_IMAGE_MODEL", fallback="google/gemini-2.5-flash-image"
)
# Parse fallback models into a list if configured
_openrouter_fallback_models = (
    [m.strip() for m in OPENROUTER_FALLBACK_MODELS.split(",") if m.strip()]
    if OPENROUTER_FALLBACK_MODELS
    else None
)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Always import standard OpenAI first to ensure Sentry can instrument it
from openai import OpenAI as StandardOpenAI  # noqa: E402

# Try to import PostHog's OpenAI wrapper for LLM analytics
try:
    from posthog.ai.openai import OpenAI as PostHogOpenAI

    _posthog_available = True
    _posthog_client = analytics.posthog
    _posthog_wrappers: tuple[type, ...] = (PostHogOpenAI,)
    logger.info("[ai] PostHog LLM analytics enabled")
except ImportError:
    PostHogOpenAI = StandardOpenAI  # Fallback to standard OpenAI if PostHog not available
    _posthog_available = False
    _posthog_client = None
    _posthog_wrappers = ()
    logger.warning("[ai] PostHog AI module not available, using standard OpenAI client")

# Initialize clients with PostHog instrumentation (if available)
_openai_client = None
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
    _openrouter_client = PostHogOpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=app_config.get("OPENROUTER", "API_KEY"),
        posthog_client=_posthog_client,
    )
    logger.info(f"[ai] OpenRouter client initialized with model {OPENROUTER_MODEL}")
except Exception as e:
    logger.debug(f"[ai] Failed to initialize OpenRouter client: {e}")
    try:
        _openrouter_client = StandardOpenAI(
            base_url=OPENROUTER_BASE_URL,
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


async def _call_callback(callback: Callable[..., Awaitable[None] | None], *args):
    """Helper to call callback whether it's sync or async."""
    result = callback(*args)
    if inspect.isawaitable(result):
        await result


# Hard cap on model <-> tool round trips per request, so a model that keeps
# calling tools can't loop forever
MAX_TOOL_ROUNDS = 8
# Once a request has spent this long, the model has to answer with what it has
TOOL_TIME_BUDGET_SECONDS = 90


@dataclass
class LLMAttachment:
    """A file sent to the model alongside the prompt - an image or a PDF."""

    data: bytes
    mime_type: str
    filename: str | None = None

    @property
    def is_image(self) -> bool:
        return self.mime_type.startswith("image/")

    def data_url(self) -> str:
        return f"data:{self.mime_type};base64,{base64.b64encode(bytes(self.data)).decode('utf-8')}"

    def to_openai(self) -> dict:
        """The attachment as an OpenAI chat completions content part."""
        if self.is_image:
            return {"type": "image_url", "image_url": {"url": self.data_url()}}
        return {
            "type": "file",
            "file": {"filename": self.filename or "file", "file_data": self.data_url()},
        }


@dataclass
class ToolResult:
    """What a tool hands back to the model - text, plus any files it fetched."""

    text: str
    attachments: list[LLMAttachment] = field(default_factory=list)


@dataclass
class LLMTool:
    """A function the model can call while generating a response."""

    name: str
    description: str
    # JSON schema for the function's arguments
    parameters: dict
    # Called with the parsed arguments as kwargs; returns text or a ToolResult
    handler: Callable[..., str | ToolResult | Awaitable[str | ToolResult]]
    # Describes a call in progress for the user, eg. "🌐 opening example.com…"
    status: Callable[[dict], str | None] | None = None

    def to_openai(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def describe(self, arguments: dict) -> str | None:
        if self.status is None:
            return None
        try:
            return self.status(arguments)
        except Exception:
            return None


# Called when the model starts a tool call, with the tool and its arguments
ToolCallCallback = Callable[[LLMTool, dict], Awaitable[None] | None]


def _merge_attachments(
    attachments: list[LLMAttachment] | None,
    image_bytes: bytes | None,
    image_mime_type: str | None,
) -> list[LLMAttachment]:
    """Combine the attachments list with the legacy single image arguments."""
    merged = list(attachments or [])
    if image_bytes:
        merged.insert(0, LLMAttachment(bytes(image_bytes), image_mime_type or "image/jpeg"))
    return merged


def _parse_arguments(raw_arguments: str) -> tuple[dict | None, str | None]:
    """Parse a tool call's JSON arguments, returning (arguments, error)."""
    try:
        arguments = json.loads(raw_arguments) if raw_arguments else {}
        if not isinstance(arguments, dict):
            raise ValueError("arguments must be a JSON object")
        return arguments, None
    except Exception as e:
        return None, f"Error: could not parse arguments - {e}"


async def _run_tool(tool: LLMTool, arguments: dict) -> ToolResult:
    """Run a tool call, returning errors as text so the model can recover."""
    try:
        logger.info(f"[ai] Running tool {tool.name} with {arguments}")
        result = tool.handler(**arguments)
        if inspect.isawaitable(result):
            result = await result
        if isinstance(result, ToolResult):
            return result
        return ToolResult(str(result))
    except Exception as e:
        logger.warning(f"[ai] Tool {tool.name} failed: {e}")
        return ToolResult(f"Error: {e}")


def _build_openai_messages(
    message_text: str | None,
    messages: list[dict] | None,
    system_prompt: str | None,
    attachments: list[LLMAttachment] | None,
) -> list[dict]:
    """Build an OpenAI-style messages list, attaching files to the last user message."""
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
        if i == last_index and msg["role"] == "user" and attachments:
            content = [a.to_openai() for a in attachments]
            content.append({"type": "text", "text": msg["content"]})
            formatted_messages.append({"role": "user", "content": content})
        else:
            formatted_messages.append(msg)

    return formatted_messages


class LLMClient:
    """Unified interface for LLM providers (OpenRouter and OpenAI)."""

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
            provider: "openrouter" or "openai". If None, uses configured default.
            model: Model name. If None, uses configured default for provider.
            models: List of fallback model IDs for OpenRouter. If None, uses configured default.
                    Only used when provider is "openrouter".
            distinct_id: Telegram user ID the generations are attributed to in PostHog.
            properties: Extra properties attached to the PostHog $ai_generation events.
            _client: Optional client override (for internal use).
        """
        self.provider = provider or AI_PROVIDER
        if self.provider not in SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported provider: {self.provider}")
        self.distinct_id = distinct_id
        self.properties = properties or {}
        self._client_override = _client
        if self.provider == "openrouter":
            self.model = model or OPENROUTER_MODEL
            # Use provided models, or fall back to configured defaults
            self.models = models if models is not None else _openrouter_fallback_models
        else:
            self.model = model or OPENAI_MODEL
            self.models = None  # Fallback models not supported for OpenAI

        if self._client_override is None:
            if self.provider == "openai" and _openai_client is None:
                raise ValueError("OpenAI client is not configured.")
            if self.provider == "openrouter" and _openrouter_client is None:
                raise ValueError("OpenRouter client is not configured.")

    def _client(self):
        client = self._client_override or (
            _openrouter_client if self.provider == "openrouter" else _openai_client
        )
        assert client is not None, f"{self.provider} client not configured"
        return client

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

    def _extra_body(self, attachments: list[LLMAttachment] | None = None) -> dict:
        """OpenRouter-specific request options - fallback models and the PDF parser."""
        if self.provider != "openrouter":
            return {}
        extra_body = {}
        if self.models:
            extra_body["models"] = self.models
        if any(not a.is_image for a in attachments or []):
            extra_body["plugins"] = [
                {"id": "file-parser", "pdf": {"engine": OPENROUTER_PDF_ENGINE}}
            ]
        return extra_body

    def _server_tools(self) -> list[dict]:
        """Tools OpenRouter runs itself, on our behalf."""
        if self.provider != "openrouter":
            return []
        server_tools = []
        if OPENROUTER_WEB_SEARCH:
            server_tools.append({"type": "openrouter:web_search"})
        server_tools.append({"type": "openrouter:datetime"})
        return server_tools

    @property
    def has_web_search(self) -> bool:
        """Whether responses from this client can use real-time web search."""
        return self.provider == "openrouter" and OPENROUTER_WEB_SEARCH

    async def generate_streaming(
        self,
        message_text: str | None = None,
        messages: list[dict] | None = None,
        system_prompt: str | None = None,
        image_bytes: bytes | None = None,
        image_mime_type: str | None = None,
        on_chunk: Callable[[str], Awaitable[None] | None] | None = None,
        update_interval: float = 1.0,
        tools: list[LLMTool] | None = None,
        attachments: list[LLMAttachment] | None = None,
        on_tool_call: ToolCallCallback | None = None,
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
            tools: Optional functions the model may call.
            attachments: Optional images / PDFs to send with the last user message.
            on_tool_call: Optional callback invoked as each tool call starts.

        Returns:
            Complete response text.
        """
        if not messages and not message_text:
            raise ValueError("Either message_text or messages must be provided")

        attachments = _merge_attachments(attachments, image_bytes, image_mime_type)
        client = self._client()

        extra_kwargs = self._posthog_kwargs(client)
        extra_body = self._extra_body(attachments)
        if extra_body:
            extra_kwargs["extra_body"] = extra_body

        return await self._stream_chat_completion(
            client=client,
            formatted_messages=_build_openai_messages(
                message_text, messages, system_prompt, attachments
            ),
            extra_kwargs=extra_kwargs,
            server_tools=self._server_tools(),
            tools=tools,
            on_chunk=on_chunk,
            update_interval=update_interval,
            on_tool_call=on_tool_call,
        )

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
        attachments = _merge_attachments(None, image_bytes, image_mime_type)
        content = [a.to_openai() for a in attachments]
        content.append({"type": "text", "text": message_text})

        create_kwargs = {
            "model": self.model,
            "messages": [{"role": "user", "content": content}],
            "stream": False,
            "max_completion_tokens": 2000,
        }
        extra_body = self._extra_body(attachments)
        if extra_body:
            create_kwargs["extra_body"] = extra_body
        server_tools = self._server_tools()
        if server_tools:
            create_kwargs["tools"] = server_tools

        client = self._client()
        response = await asyncio.to_thread(
            client.chat.completions.create, **create_kwargs, **self._posthog_kwargs(client)
        )
        return LLMResponse(response.choices[0].message.content or "", self.provider)

    async def complete(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        max_tokens: int = 1000,
    ) -> str:
        """Plain non-streaming completion - no tools, no web search."""
        create_kwargs = {
            "model": self.model,
            "messages": _build_openai_messages(None, messages, system_prompt, None),
            "stream": False,
            "max_completion_tokens": max_tokens,
        }
        extra_body = self._extra_body()
        if extra_body:
            create_kwargs["extra_body"] = extra_body

        client = self._client()
        response = await asyncio.to_thread(
            client.chat.completions.create, **create_kwargs, **self._posthog_kwargs(client)
        )
        return response.choices[0].message.content or ""

    async def _stream_chat_completion(
        self,
        client,
        formatted_messages: list[dict],
        extra_kwargs: dict,
        server_tools: list[dict],
        tools: list[LLMTool] | None,
        on_chunk: Callable[[str], Awaitable[None] | None] | None,
        update_interval: float,
        on_tool_call: ToolCallCallback | None = None,
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
        deadline = time.monotonic() + TOOL_TIME_BUDGET_SECONDS

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
            out_of_budget = round_num == MAX_TOOL_ROUNDS or time.monotonic() > deadline
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
            if tool_map and out_of_budget:
                # Out of tool rounds or time - make the model answer with what it has
                create_kwargs["tool_choice"] = "none"

            response_text, tool_calls = await asyncio.to_thread(consume, create_kwargs)

            # Server-side tools (eg. openrouter:web_search) are resolved by the
            # provider, so only our own function tools need a round trip
            own_calls = [c for c in tool_calls.values() if c["name"] in tool_map]
            if not own_calls or out_of_budget:
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

            fetched: list[LLMAttachment] = []
            for call in own_calls:
                tool = tool_map[call["name"]]
                arguments, error = _parse_arguments(call["arguments"])
                if arguments is None:
                    logger.warning(
                        f"[ai] Bad arguments for tool {tool.name}: {call['arguments']!r}"
                    )
                    result = ToolResult(error or "Error: bad arguments")
                else:
                    if on_tool_call:
                        with contextlib.suppress(Exception):
                            await _call_callback(on_tool_call, tool, arguments)
                    result = await _run_tool(tool, arguments)
                conversation.append(
                    {"role": "tool", "tool_call_id": call["id"], "content": result.text}
                )
                fetched += result.attachments

            # Tool messages can only carry text, so files the tools fetched are
            # handed over in a follow-up user message
            if fetched:
                conversation.append(
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Files fetched by the tool calls above:"},
                            *(a.to_openai() for a in fetched),
                        ],
                    }
                )
                plugins = self._extra_body(fetched).get("plugins")
                if plugins:
                    extra_kwargs["extra_body"] = {
                        **extra_kwargs.get("extra_body", {}),
                        "plugins": plugins,
                    }

        if on_chunk:
            with contextlib.suppress(Exception):
                await _call_callback(on_chunk, response_text)

        return response_text


async def generate_image(prompt: str) -> LLMAttachment:
    """Generate an image from a text prompt with OpenRouter's image API."""

    def post() -> dict:
        response = requests.post(
            f"{OPENROUTER_BASE_URL}/images",
            headers={"Authorization": f"Bearer {app_config.get('OPENROUTER', 'API_KEY')}"},
            json={"model": OPENROUTER_IMAGE_MODEL, "prompt": prompt},
            timeout=120,
        )
        if not response.ok:
            raise RuntimeError(
                f"image generation failed ({response.status_code}): {response.text[:300]}"
            )
        return response.json()

    body = await asyncio.to_thread(post)
    image = body["data"][0]
    return LLMAttachment(
        data=base64.b64decode(image["b64_json"]),
        mime_type=image.get("media_type") or "image/png",
    )


def get_default_client(distinct_id: str | None = None, properties: dict | None = None) -> LLMClient:
    """Get default LLM client based on configuration."""
    return LLMClient(distinct_id=distinct_id, properties=properties)


def get_openai_client(
    model: str | None = None, distinct_id: str | None = None, properties: dict | None = None
) -> LLMClient:
    """Get OpenAI client with optional custom model."""
    return LLMClient(provider="openai", model=model, distinct_id=distinct_id, properties=properties)


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
