"""Tests for the unified LLM interface wrapper."""

import base64
from unittest.mock import MagicMock, patch

import pytest

from src.domain import ai


class TestLLMResponse:
    """Test LLMResponse class."""

    def test_llm_response_initialization(self):
        """Test LLMResponse initialization."""
        response = ai.LLMResponse(text="Hello", provider="openai")
        assert response.text == "Hello"
        assert response.provider == "openai"

    def test_llm_response_different_providers(self):
        """Test LLMResponse with different providers."""
        response1 = ai.LLMResponse(text="Test", provider="openai")
        response2 = ai.LLMResponse(text="Test", provider="openrouter")
        response3 = ai.LLMResponse(text="Test", provider="openrouter")

        assert response1.provider == "openai"
        assert response2.provider == "openrouter"
        assert response3.provider == "openrouter"


class TestCallCallback:
    """Test _call_callback helper function."""

    @pytest.mark.anyio
    async def test_call_callback_sync(self):
        """Test calling a sync callback."""
        callback_called = []

        def sync_callback(text: str):
            callback_called.append(text)

        await ai._call_callback(sync_callback, "test")
        assert callback_called == ["test"]

    @pytest.mark.anyio
    async def test_call_callback_async(self):
        """Test calling an async callback."""
        callback_called = []

        async def async_callback(text: str):
            callback_called.append(text)

        await ai._call_callback(async_callback, "test")
        assert callback_called == ["test"]


class TestLLMClientInitialization:
    """Test LLMClient initialization."""

    @patch("src.domain.ai._openai_client")
    @patch("src.domain.ai.AI_PROVIDER", "openai")
    def test_init_openai_client(self, mock_client):
        """Test initializing OpenAI client."""
        mock_client.__bool__ = lambda x: True
        client = ai.LLMClient(provider="openai")
        assert client.provider == "openai"
        assert client.model is not None

    @patch("src.domain.ai._openrouter_client")
    @patch("src.domain.ai.AI_PROVIDER", "openrouter")
    def test_init_openrouter_client(self, mock_client):
        """Test initializing OpenRouter client."""
        mock_client.__bool__ = lambda x: True
        client = ai.LLMClient(provider="openrouter")
        assert client.provider == "openrouter"
        assert client.model is not None

    @patch("src.domain.ai._openai_client", None)
    def test_init_openai_client_not_configured(self):
        """Test initializing OpenAI client when not configured."""
        with pytest.raises(ValueError, match="OpenAI client is not configured"):
            ai.LLMClient(provider="openai")

    @patch("src.domain.ai._openrouter_client", None)
    def test_init_openrouter_client_not_configured(self):
        """Test initializing OpenRouter client when not configured."""
        with pytest.raises(ValueError, match="OpenRouter client is not configured"):
            ai.LLMClient(provider="openrouter")

    @patch("src.domain.ai._openai_client")
    def test_init_with_custom_model(self, mock_client):
        """Test initializing client with custom model."""
        mock_client.__bool__ = lambda x: True
        client = ai.LLMClient(provider="openai", model="custom-model")
        assert client.model == "custom-model"

    @patch("src.domain.ai._openai_client")
    @patch("src.domain.ai.AI_PROVIDER", "openai")
    def test_init_default_provider(self, mock_client):
        """Test initializing with default provider."""
        mock_client.__bool__ = lambda x: True
        client = ai.LLMClient()
        assert client.provider == "openai"


class TestLLMClientGenerate:
    """Test LLMClient.generate method."""

    @pytest.mark.anyio
    @patch("src.domain.ai._openai_client")
    async def test_generate_openai(self, mock_client):
        """Test generating response from OpenAI."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "OpenAI response"

        mock_client.chat.completions.create = MagicMock(return_value=mock_response)
        mock_client.__bool__ = lambda x: True

        client = ai.LLMClient(provider="openai")
        response = await client.generate("Hello")

        assert isinstance(response, ai.LLMResponse)
        assert response.text == "OpenAI response"
        assert response.provider == "openai"
        mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.anyio
    @patch("src.domain.ai._openrouter_client")
    async def test_generate_openrouter(self, mock_client):
        """Test generating response from OpenRouter."""
        # Mock OpenRouter response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "OpenRouter response"

        mock_client.chat.completions.create = MagicMock(return_value=mock_response)
        mock_client.__bool__ = lambda x: True

        client = ai.LLMClient(provider="openrouter")
        response = await client.generate("Hello")

        assert isinstance(response, ai.LLMResponse)
        assert response.text == "OpenRouter response"
        assert response.provider == "openrouter"
        mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.anyio
    @patch("src.domain.ai._openai_client")
    async def test_generate_with_image(self, mock_client):
        """Test generating response with image."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Image response"

        mock_client.chat.completions.create = MagicMock(return_value=mock_response)
        mock_client.__bool__ = lambda x: True

        client = ai.LLMClient(provider="openai")
        image_bytes = b"fake_image_data"
        response = await client.generate("Describe this", image_bytes=image_bytes)

        assert response.text == "Image response"
        # Verify image was included in the request
        call_args = mock_client.chat.completions.create.call_args
        content = call_args[1]["messages"][0]["content"]
        assert len(content) == 2  # Image + text
        assert content[0]["type"] == "image_url"

    @pytest.mark.anyio
    @patch("src.domain.ai._openai_client")
    async def test_generate_openai_empty_response(self, mock_client):
        """Test handling empty OpenAI response."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None

        mock_client.chat.completions.create = MagicMock(return_value=mock_response)
        mock_client.__bool__ = lambda x: True

        client = ai.LLMClient(provider="openai")
        response = await client.generate("Hello")

        assert response.text == ""

    @pytest.mark.anyio
    @patch("src.domain.ai._openai_client")
    async def test_generate_unsupported_provider(self, mock_client):
        """Unknown providers (eg. the removed gemini) are rejected."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            ai.LLMClient(provider="gemini")


class TestLLMClientGenerateStreaming:
    """Test LLMClient.generate_streaming method."""

    @pytest.mark.anyio
    @patch("src.domain.ai._openai_client")
    async def test_generate_streaming_openai(self, mock_client):
        """Test streaming response from OpenAI."""
        # Mock streaming chunks
        mock_chunk1 = MagicMock()
        mock_chunk1.choices = [MagicMock()]
        mock_chunk1.choices[0].delta.content = "Hello "

        mock_chunk2 = MagicMock()
        mock_chunk2.choices = [MagicMock()]
        mock_chunk2.choices[0].delta.content = "World"

        mock_stream = [mock_chunk1, mock_chunk2]
        mock_client.chat.completions.create.return_value = mock_stream
        mock_client.__bool__ = lambda x: True

        client = ai.LLMClient(provider="openai")
        response = await client.generate_streaming("Hello")

        assert response == "Hello World"

    @pytest.mark.anyio
    @patch("src.domain.ai._openrouter_client")
    async def test_generate_streaming_openrouter(self, mock_client):
        """Test streaming response from OpenRouter."""
        # Mock streaming chunks
        mock_chunk1 = MagicMock()
        mock_chunk1.choices = [MagicMock()]
        mock_chunk1.choices[0].delta.content = "OpenRouter "

        mock_chunk2 = MagicMock()
        mock_chunk2.choices = [MagicMock()]
        mock_chunk2.choices[0].delta.content = "response"

        mock_stream = [mock_chunk1, mock_chunk2]
        mock_client.chat.completions.create.return_value = mock_stream
        mock_client.__bool__ = lambda x: True

        client = ai.LLMClient(provider="openrouter")
        response = await client.generate_streaming("Hello")

        assert response == "OpenRouter response"

    @pytest.mark.anyio
    @patch("src.domain.ai._openai_client")
    async def test_generate_streaming_with_callback(self, mock_client):
        """Test streaming with callback function."""
        # Mock streaming chunks
        mock_chunk1 = MagicMock()
        mock_chunk1.choices = [MagicMock()]
        mock_chunk1.choices[0].delta.content = "Hello "

        mock_chunk2 = MagicMock()
        mock_chunk2.choices = [MagicMock()]
        mock_chunk2.choices[0].delta.content = "World"

        mock_stream = [mock_chunk1, mock_chunk2]
        mock_client.chat.completions.create.return_value = mock_stream
        mock_client.__bool__ = lambda x: True

        callback_calls = []

        async def callback(text: str):
            callback_calls.append(text)

        client = ai.LLMClient(provider="openai")
        response = await client.generate_streaming("Hello", on_chunk=callback)

        assert response == "Hello World"
        # Callback should be called at least once (final call)
        assert len(callback_calls) > 0
        assert callback_calls[-1] == "Hello World"

    @pytest.mark.anyio
    @patch("src.domain.ai._openai_client")
    async def test_generate_streaming_with_image(self, mock_client):
        """Test streaming with image."""
        # Mock streaming chunks
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta.content = "Image description"

        mock_stream = [mock_chunk]
        mock_client.chat.completions.create.return_value = mock_stream
        mock_client.__bool__ = lambda x: True

        client = ai.LLMClient(provider="openai")
        image_bytes = b"fake_image_data"
        response = await client.generate_streaming("Describe", image_bytes=image_bytes)

        assert response == "Image description"
        # Verify image was included
        call_args = mock_client.chat.completions.create.call_args
        content = call_args[1]["messages"][0]["content"]
        assert len(content) == 2  # Image + text

    @pytest.mark.anyio
    @patch("src.domain.ai._openai_client")
    async def test_generate_streaming_chunks_with_none_content(self, mock_client):
        """Test handling chunks with None content."""
        # Mock streaming chunks with None content
        mock_chunk1 = MagicMock()
        mock_chunk1.choices = [MagicMock()]
        mock_chunk1.choices[0].delta.content = "Hello "

        mock_chunk2 = MagicMock()
        mock_chunk2.choices = [MagicMock()]
        mock_chunk2.choices[0].delta.content = None  # None content

        mock_chunk3 = MagicMock()
        mock_chunk3.choices = [MagicMock()]
        mock_chunk3.choices[0].delta.content = "World"

        mock_stream = [mock_chunk1, mock_chunk2, mock_chunk3]
        mock_client.chat.completions.create.return_value = mock_stream
        mock_client.__bool__ = lambda x: True

        client = ai.LLMClient(provider="openai")
        response = await client.generate_streaming("Hello")

        assert response == "Hello World"  # None chunks should be skipped


class TestHelperFunctions:
    """Test helper functions."""

    @patch("src.domain.ai._openai_client")
    @patch("src.domain.ai.AI_PROVIDER", "openai")
    def test_get_default_client(self, mock_client):
        """Test get_default_client function."""
        mock_client.__bool__ = lambda x: True
        client = ai.get_default_client()
        assert isinstance(client, ai.LLMClient)

    @patch("src.domain.ai._openai_client")
    def test_get_openai_client(self, mock_client):
        """Test get_openai_client function."""
        mock_client.__bool__ = lambda x: True
        client = ai.get_openai_client()
        assert isinstance(client, ai.LLMClient)
        assert client.provider == "openai"

    @patch("src.domain.ai._openai_client")
    def test_get_openai_client_with_model(self, mock_client):
        """Test get_openai_client with custom model."""
        mock_client.__bool__ = lambda x: True
        client = ai.get_openai_client(model="custom-model")
        assert client.model == "custom-model"

    @patch("src.domain.ai._openrouter_client")
    def test_get_openrouter_client(self, mock_client):
        """Test get_openrouter_client function."""
        mock_client.__bool__ = lambda x: True
        client = ai.get_openrouter_client()
        assert isinstance(client, ai.LLMClient)
        assert client.provider == "openrouter"

    @patch("src.domain.ai._openrouter_client")
    def test_get_openrouter_client_with_model(self, mock_client):
        """Test get_openrouter_client with custom model."""
        mock_client.__bool__ = lambda x: True
        client = ai.get_openrouter_client(model="custom-model")
        assert client.model == "custom-model"


class TestImageHandling:
    """Test image handling in requests."""

    @pytest.mark.anyio
    @patch("src.domain.ai._openai_client")
    async def test_image_base64_encoding(self, mock_client):
        """Test that images are properly base64 encoded."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"

        mock_client.chat.completions.create = MagicMock(return_value=mock_response)
        mock_client.__bool__ = lambda x: True

        client = ai.LLMClient(provider="openai")
        image_bytes = b"fake_image_data"
        await client.generate("Test", image_bytes=image_bytes)

        # Verify the call was made
        call_args = mock_client.chat.completions.create.call_args
        content = call_args[1]["messages"][0]["content"]
        image_url = content[0]["image_url"]["url"]

        # Check that it's a data URL with base64
        assert image_url.startswith("data:image/jpeg;base64,")
        base64_data = image_url.split(",")[1]
        # Verify it's valid base64
        decoded = base64.b64decode(base64_data)
        assert decoded == image_bytes


def _text_chunk(text):
    chunk = MagicMock()
    chunk.choices = [MagicMock()]
    chunk.choices[0].delta.content = text
    chunk.choices[0].delta.tool_calls = None
    return chunk


def _tool_call_chunk(index, call_id, name, arguments):
    tool_call = MagicMock()
    tool_call.index = index
    tool_call.id = call_id
    tool_call.function.name = name
    tool_call.function.arguments = arguments
    chunk = MagicMock()
    chunk.choices = [MagicMock()]
    chunk.choices[0].delta.content = None
    chunk.choices[0].delta.tool_calls = [tool_call]
    return chunk


def _tool(handler, name="get_chat_history"):
    return ai.LLMTool(
        name=name,
        description="Read the chat",
        parameters={"type": "object", "properties": {}},
        handler=handler,
    )


class TestLLMClientTools:
    """Test tool calling in LLMClient.generate_streaming."""

    @pytest.mark.anyio
    @patch("src.domain.ai._openrouter_client")
    async def test_runs_tool_and_feeds_result_back(self, mock_client):
        mock_client.chat.completions.create.side_effect = [
            [
                _tool_call_chunk(0, "call_1", "get_chat_history", '{"lim'),
                _tool_call_chunk(0, None, None, 'it": 5}'),
            ],
            [_text_chunk("They were "), _text_chunk("talking about chai")],
        ]
        calls = []

        def handler(limit):
            calls.append(limit)
            return "[#1] @minji: chai?"

        client = ai.LLMClient(provider="openrouter")
        response = await client.generate_streaming(
            messages=[{"role": "user", "content": "what's up?"}], tools=[_tool(handler)]
        )

        assert response == "They were talking about chai"
        assert calls == [5]

        second_call = mock_client.chat.completions.create.call_args_list[1].kwargs
        assistant_msg, tool_msg = second_call["messages"][-2:]
        assert assistant_msg["tool_calls"][0]["id"] == "call_1"
        assert assistant_msg["tool_calls"][0]["function"]["arguments"] == '{"limit": 5}'
        assert tool_msg == {
            "role": "tool",
            "tool_call_id": "call_1",
            "content": "[#1] @minji: chai?",
        }
        # Server tools and function tools are sent together
        tool_types = [t["type"] for t in second_call["tools"]]
        assert "openrouter:datetime" in tool_types
        assert "function" in tool_types

    @pytest.mark.anyio
    @patch("src.domain.ai._openai_client")
    async def test_async_tool_handler(self, mock_client):
        mock_client.chat.completions.create.side_effect = [
            [_tool_call_chunk(0, "call_1", "get_chat_history", "{}")],
            [_text_chunk("done")],
        ]

        async def handler():
            return "result"

        client = ai.LLMClient(provider="openai")
        response = await client.generate_streaming("hi", tools=[_tool(handler)])

        assert response == "done"
        tool_msg = mock_client.chat.completions.create.call_args_list[1].kwargs["messages"][-1]
        assert tool_msg["content"] == "result"

    @pytest.mark.anyio
    @patch("src.domain.ai._openai_client")
    async def test_tool_errors_are_returned_to_model(self, mock_client):
        mock_client.chat.completions.create.side_effect = [
            [
                _tool_call_chunk(0, "call_1", "get_chat_history", "not json"),
                _tool_call_chunk(1, "call_2", "boom", "{}"),
            ],
            [_text_chunk("sorry")],
        ]

        def boom():
            raise RuntimeError("kaboom")

        client = ai.LLMClient(provider="openai")
        response = await client.generate_streaming(
            "hi", tools=[_tool(lambda: "unused"), _tool(boom, name="boom")]
        )

        assert response == "sorry"
        messages = mock_client.chat.completions.create.call_args_list[1].kwargs["messages"]
        assert messages[-2]["content"].startswith("Error: could not parse arguments")
        assert messages[-1]["content"] == "Error: kaboom"

    @pytest.mark.anyio
    @patch("src.domain.ai._openrouter_client")
    async def test_server_tool_calls_are_not_looped(self, mock_client):
        mock_client.chat.completions.create.return_value = [
            _tool_call_chunk(0, "srv_1", "web_search", "{}"),
            _text_chunk("answer"),
        ]

        client = ai.LLMClient(provider="openrouter")
        response = await client.generate_streaming("hi", tools=[_tool(lambda: "x")])

        assert response == "answer"
        assert mock_client.chat.completions.create.call_count == 1

    @pytest.mark.anyio
    @patch("src.domain.ai._openai_client")
    async def test_tool_rounds_are_capped(self, mock_client):
        rounds = ai.MAX_TOOL_ROUNDS + 1
        mock_client.chat.completions.create.side_effect = [
            [_tool_call_chunk(0, f"call_{i}", "get_chat_history", "{}")] for i in range(rounds)
        ]

        client = ai.LLMClient(provider="openai")
        await client.generate_streaming("hi", tools=[_tool(lambda: "more")])

        calls = mock_client.chat.completions.create.call_args_list
        assert len(calls) == rounds
        assert calls[-1].kwargs["tool_choice"] == "none"
        assert "tool_choice" not in calls[0].kwargs

    @pytest.mark.anyio
    @patch("src.domain.ai._openai_client")
    async def test_no_tools_kwarg_without_tools(self, mock_client):
        mock_client.chat.completions.create.return_value = [_text_chunk("hi")]

        client = ai.LLMClient(provider="openai")
        await client.generate_streaming("hi")

        assert "tools" not in mock_client.chat.completions.create.call_args.kwargs

    @pytest.mark.anyio
    @patch("src.domain.ai._openai_client")
    async def test_streams_intermediate_updates(self, mock_client):
        mock_client.chat.completions.create.return_value = [
            _text_chunk("a"),
            _text_chunk("b"),
            _text_chunk("c"),
        ]
        updates = []

        async def on_chunk(text):
            updates.append(text)

        client = ai.LLMClient(provider="openai")
        await client.generate_streaming("hi", on_chunk=on_chunk, update_interval=0)

        assert updates == ["a", "ab", "abc", "abc"]

    @pytest.mark.anyio
    @patch("src.domain.ai._openai_client")
    async def test_image_only_on_last_message(self, mock_client):
        mock_client.chat.completions.create.return_value = [_text_chunk("ok")]
        messages = [
            {"role": "user", "content": "same"},
            {"role": "assistant", "content": "reply"},
            {"role": "user", "content": "same"},
        ]

        client = ai.LLMClient(provider="openai")
        await client.generate_streaming(messages=messages, image_bytes=b"img")

        sent = mock_client.chat.completions.create.call_args.kwargs["messages"]
        assert sent[0]["content"] == "same"
        assert isinstance(sent[2]["content"], list)

    @patch("src.domain.ai._openrouter_client")
    @patch("src.domain.ai._openai_client")
    def test_has_web_search(self, mock_openai, mock_openrouter):
        with patch("src.domain.ai.OPENROUTER_WEB_SEARCH", True):
            assert ai.LLMClient(provider="openrouter").has_web_search is True
            assert ai.LLMClient(provider="openai").has_web_search is False
        with patch("src.domain.ai.OPENROUTER_WEB_SEARCH", False):
            assert ai.LLMClient(provider="openrouter").has_web_search is False


class _FakePostHogWrapper:
    """Stands in for a PostHog-wrapped provider client."""

    def __init__(self):
        self.chat = MagicMock()
        self.models = MagicMock()


class TestPostHogTracking:
    """Test PostHog AI observability kwargs on LLM requests."""

    def test_no_posthog_kwargs_for_unwrapped_client(self):
        client = ai.LLMClient(provider="openai", distinct_id="42", _client=MagicMock())
        assert client._posthog_kwargs(MagicMock()) == {}

    @patch("src.domain.ai._posthog_wrappers", (_FakePostHogWrapper,))
    def test_posthog_kwargs_for_wrapped_client(self):
        wrapped = _FakePostHogWrapper()
        client = ai.LLMClient(
            provider="openai", distinct_id="42", properties={"command": "ai"}, _client=wrapped
        )

        kwargs = client._posthog_kwargs(wrapped)

        assert kwargs["posthog_distinct_id"] == "42"
        assert kwargs["posthog_properties"] == {"provider": "openai", "command": "ai"}
        assert kwargs["posthog_trace_id"]
        # Each request is its own trace
        assert client._posthog_kwargs(wrapped)["posthog_trace_id"] != kwargs["posthog_trace_id"]

    @pytest.mark.anyio
    @patch("src.domain.ai._posthog_wrappers", (_FakePostHogWrapper,))
    async def test_tool_rounds_share_one_trace(self):
        wrapped = _FakePostHogWrapper()
        wrapped.chat.completions.create.side_effect = [
            [_tool_call_chunk(0, "call_1", "get_chat_history", "{}")],
            [_text_chunk("done")],
        ]
        client = ai.LLMClient(provider="openrouter", distinct_id="42", _client=wrapped)

        await client.generate_streaming(
            messages=[{"role": "user", "content": "hi"}], tools=[_tool(lambda: "history")]
        )

        first, second = [c.kwargs for c in wrapped.chat.completions.create.call_args_list]
        assert first["posthog_distinct_id"] == second["posthog_distinct_id"] == "42"
        assert first["posthog_trace_id"] == second["posthog_trace_id"]


class TestAttachments:
    """Test sending images and PDFs with a request."""

    def test_image_part(self):
        part = ai.LLMAttachment(b"png", "image/png").to_openai()
        assert part == {
            "type": "image_url",
            "image_url": {"url": "data:image/png;base64," + base64.b64encode(b"png").decode()},
        }

    def test_pdf_part(self):
        part = ai.LLMAttachment(b"%PDF", "application/pdf", filename="a.pdf").to_openai()
        assert part["type"] == "file"
        assert part["file"]["filename"] == "a.pdf"
        assert part["file"]["file_data"].startswith("data:application/pdf;base64,")

    def test_legacy_image_bytes_merged_first(self):
        pdf = ai.LLMAttachment(b"%PDF", "application/pdf")
        merged = ai._merge_attachments([pdf], b"img", None)
        assert merged == [ai.LLMAttachment(b"img", "image/jpeg"), pdf]

    @pytest.mark.anyio
    @patch("src.domain.ai._openrouter_client")
    async def test_openrouter_sends_attachments_with_pdf_parser(self, mock_client):
        mock_client.chat.completions.create.return_value = [_text_chunk("ok")]
        attachments = [
            ai.LLMAttachment(b"img", "image/webp"),
            ai.LLMAttachment(b"%PDF", "application/pdf", filename="a.pdf"),
        ]

        client = ai.LLMClient(provider="openrouter", models=[])
        await client.generate_streaming(
            messages=[{"role": "user", "content": "summarise"}], attachments=attachments
        )

        kwargs = mock_client.chat.completions.create.call_args.kwargs
        content = kwargs["messages"][0]["content"]
        assert [p["type"] for p in content] == ["image_url", "file", "text"]
        assert content[0]["image_url"]["url"].startswith("data:image/webp;base64,")
        assert kwargs["extra_body"] == {
            "plugins": [{"id": "file-parser", "pdf": {"engine": ai.OPENROUTER_PDF_ENGINE}}]
        }

    @pytest.mark.anyio
    @patch("src.domain.ai._openrouter_client")
    async def test_openrouter_images_only_skip_pdf_parser(self, mock_client):
        mock_client.chat.completions.create.return_value = [_text_chunk("ok")]

        client = ai.LLMClient(provider="openrouter", models=[])
        await client.generate_streaming(
            "describe", attachments=[ai.LLMAttachment(b"img", "image/jpeg")]
        )

        assert "extra_body" not in mock_client.chat.completions.create.call_args.kwargs


class TestAgentLoop:
    """Tool results with files, progress callbacks and the time budget."""

    @pytest.mark.anyio
    @patch("src.domain.ai._openrouter_client")
    async def test_tool_files_are_handed_to_the_model(self, mock_client):
        mock_client.chat.completions.create.side_effect = [
            [_tool_call_chunk(0, "call_1", "get_chat_history", "{}")],
            [_text_chunk("nice pic")],
        ]
        image = ai.LLMAttachment(b"img", "image/png")
        pdf = ai.LLMAttachment(b"%PDF", "application/pdf", filename="a.pdf")

        client = ai.LLMClient(provider="openrouter", models=[])
        response = await client.generate_streaming(
            "look", tools=[_tool(lambda: ai.ToolResult("found it", [image, pdf]))]
        )

        assert response == "nice pic"
        second = mock_client.chat.completions.create.call_args_list[1].kwargs
        tool_msg, files_msg = second["messages"][-2:]
        assert tool_msg["content"] == "found it"
        assert files_msg["role"] == "user"
        assert [p["type"] for p in files_msg["content"]] == ["text", "image_url", "file"]
        # A fetched PDF turns on the PDF parser for the following rounds
        assert second["extra_body"]["plugins"][0]["id"] == "file-parser"

    @pytest.mark.anyio
    @patch("src.domain.ai._openai_client")
    async def test_on_tool_call_gets_tool_and_arguments(self, mock_client):
        mock_client.chat.completions.create.side_effect = [
            [_tool_call_chunk(0, "call_1", "get_chat_history", '{"limit": 3}')],
            [_text_chunk("ok")],
        ]
        seen = []
        tool = _tool(lambda limit: "x")

        client = ai.LLMClient(provider="openai")
        await client.generate_streaming(
            "hi", tools=[tool], on_tool_call=lambda t, args: seen.append((t, args))
        )

        assert seen == [(tool, {"limit": 3})]

    @pytest.mark.anyio
    @patch("src.domain.ai._openai_client")
    async def test_on_tool_call_errors_dont_stop_the_tool(self, mock_client):
        mock_client.chat.completions.create.side_effect = [
            [_tool_call_chunk(0, "call_1", "get_chat_history", "{}")],
            [_text_chunk("ok")],
        ]
        calls = []

        def boom(tool, args):
            raise RuntimeError("telegram down")

        client = ai.LLMClient(provider="openai")
        await client.generate_streaming(
            "hi", tools=[_tool(lambda: calls.append(1) or "x")], on_tool_call=boom
        )

        assert calls == [1]

    @pytest.mark.anyio
    @patch("src.domain.ai._openai_client")
    async def test_time_budget_forces_an_answer(self, mock_client):
        mock_client.chat.completions.create.side_effect = [
            [_tool_call_chunk(0, "call_1", "get_chat_history", "{}")],
            [_text_chunk("out of time")],
        ]

        client = ai.LLMClient(provider="openai")
        with patch("src.domain.ai.TOOL_TIME_BUDGET_SECONDS", -1):
            response = await client.generate_streaming("hi", tools=[_tool(lambda: "x")])

        # The first round is already over budget, so tools are switched off
        calls = mock_client.chat.completions.create.call_args_list
        assert len(calls) == 1
        assert calls[0].kwargs["tool_choice"] == "none"
        assert response == ""

    def test_tool_describe(self):
        tool = _tool(lambda: "x")
        assert tool.describe({}) is None
        tool.status = lambda args: f"doing {args['what']}"
        assert tool.describe({"what": "stuff"}) == "doing stuff"
        # A broken status never breaks the request
        assert tool.describe({}) is None


class TestCompleteAndImages:
    @pytest.mark.anyio
    @patch("src.domain.ai._openrouter_client")
    async def test_complete_sends_no_tools(self, mock_client):
        response = MagicMock()
        response.choices[0].message.content = "summary"
        mock_client.chat.completions.create.return_value = response

        client = ai.LLMClient(provider="openrouter", models=[])
        text = await client.complete([{"role": "user", "content": "sum up"}], "be brief")

        assert text == "summary"
        kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert "tools" not in kwargs
        assert kwargs["messages"][0] == {"role": "system", "content": "be brief"}
        assert kwargs["stream"] is False

    @pytest.mark.anyio
    @patch("src.domain.ai.requests.post")
    async def test_generate_image(self, mock_post):
        mock_post.return_value.ok = True
        mock_post.return_value.json.return_value = {
            "data": [{"b64_json": base64.b64encode(b"png").decode(), "media_type": "image/png"}]
        }

        image = await ai.generate_image("a cat")

        assert image == ai.LLMAttachment(b"png", "image/png")
        body = mock_post.call_args.kwargs["json"]
        assert body == {"model": ai.OPENROUTER_IMAGE_MODEL, "prompt": "a cat"}
        assert mock_post.call_args.args[0].endswith("/images")

    @pytest.mark.anyio
    @patch("src.domain.ai.requests.post")
    async def test_generate_image_error(self, mock_post):
        mock_post.return_value.ok = False
        mock_post.return_value.status_code = 402
        mock_post.return_value.text = "insufficient credits"

        with pytest.raises(RuntimeError, match="402"):
            await ai.generate_image("a cat")
