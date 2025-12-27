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
        response2 = ai.LLMResponse(text="Test", provider="gemini")
        response3 = ai.LLMResponse(text="Test", provider="openrouter")

        assert response1.provider == "openai"
        assert response2.provider == "gemini"
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

    @patch("src.domain.ai._gemini_client")
    @patch("src.domain.ai.AI_PROVIDER", "gemini")
    def test_init_gemini_client(self, mock_client):
        """Test initializing Gemini client."""
        mock_client.__bool__ = lambda x: True
        client = ai.LLMClient(provider="gemini")
        assert client.provider == "gemini"
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

    @patch("src.domain.ai._gemini_client", None)
    def test_init_gemini_client_not_configured(self):
        """Test initializing Gemini client when not configured."""
        with pytest.raises(ValueError, match="Gemini client is not configured"):
            ai.LLMClient(provider="gemini")

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
    @patch("src.domain.ai._gemini_client")
    async def test_generate_gemini(self, mock_client):
        """Test generating response from Gemini."""
        # Mock Gemini response
        mock_response = MagicMock()
        mock_response.text = "Gemini response"

        mock_client.models.generate_content = MagicMock(return_value=mock_response)
        mock_client.__bool__ = lambda x: True

        client = ai.LLMClient(provider="gemini")
        response = await client.generate("Hello")

        assert isinstance(response, ai.LLMResponse)
        assert response.text == "Gemini response"
        assert response.provider == "gemini"
        mock_client.models.generate_content.assert_called_once()

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
        """Test generating with unsupported provider."""
        mock_client.__bool__ = lambda x: True
        client = ai.LLMClient(provider="openai")
        client.provider = "unsupported"

        with pytest.raises(ValueError, match="Unsupported provider"):
            await client.generate("Hello")


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
    @patch("src.domain.ai._gemini_client")
    async def test_generate_streaming_gemini_simulation(self, mock_client):
        """Test Gemini streaming simulation."""
        # Mock Gemini response
        mock_response = MagicMock()
        mock_response.text = "Gemini streaming response"

        mock_client.models.generate_content = MagicMock(return_value=mock_response)
        mock_client.__bool__ = lambda x: True

        callback_calls = []

        async def callback(text: str):
            callback_calls.append(text)

        client = ai.LLMClient(provider="gemini")
        response = await client.generate_streaming("Hello", on_chunk=callback)

        assert response == "Gemini streaming response"
        # Callback should be called for simulated streaming
        assert len(callback_calls) > 0

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

    @patch("src.domain.ai._gemini_client")
    def test_get_gemini_client(self, mock_client):
        """Test get_gemini_client function."""
        mock_client.__bool__ = lambda x: True
        client = ai.get_gemini_client()
        assert isinstance(client, ai.LLMClient)
        assert client.provider == "gemini"

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

    @pytest.mark.anyio
    @patch("src.domain.ai._gemini_client")
    async def test_gemini_image_handling(self, mock_client):
        """Test Gemini image handling."""
        mock_response = MagicMock()
        mock_response.text = "Response"

        mock_client.models.generate_content = MagicMock(return_value=mock_response)
        mock_client.__bool__ = lambda x: True

        client = ai.LLMClient(provider="gemini")
        image_bytes = b"fake_image_data"
        await client.generate("Test", image_bytes=image_bytes, image_mime_type="image/png")

        # Verify the call was made
        call_args = mock_client.models.generate_content.call_args
        contents = call_args[1]["contents"]
        # Should have image part and text part
        assert len(contents) == 2
