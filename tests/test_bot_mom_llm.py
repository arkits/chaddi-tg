from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Chat, Message, Update, User
from telegram.ext import ContextTypes

from src.bot.handlers import mom_llm
from src.domain import ai


@pytest.fixture
def mock_update():
    """Create a mock Telegram Update object for testing."""
    user = MagicMock(spec=User)
    user.id = 123456
    user.username = "testuser"
    user.first_name = "Test"

    chat = MagicMock(spec=Chat)
    chat.id = -1001234567890
    chat.type = "group"
    chat.title = "Test Group"

    message = MagicMock(spec=Message)
    message.message_id = 1
    message.from_user = user
    message.chat = chat
    message.text = "/mom3"
    message.reply_to_message = None
    message.reply_text = AsyncMock()

    update = MagicMock(spec=Update)
    update.message = message

    return update


@pytest.fixture
def mock_context():
    """Create a mock ContextTypes object for testing."""
    return MagicMock(spec=ContextTypes.DEFAULT_TYPE)


@pytest.mark.asyncio
async def test_handle_no_initiator_id(mock_update, mock_context):
    """Test mom3 handler when initiator_id is None."""
    with patch("src.bot.handlers.mom_llm.dc"):
        mock_update.message.from_user.id = None

        await mom_llm.handle(mock_update, mock_context)

        assert not mock_update.message.reply_text.called


@pytest.mark.asyncio
async def test_handle_insufficient_rokda(mock_update, mock_context):
    """Test mom3 handler when user doesn't have enough rokda."""
    with (
        patch("src.bot.handlers.mom_llm.dc"),
        patch("src.bot.handlers.mom_llm.util") as mock_util,
    ):
        mock_util.paywall_user.return_value = False

        reply_user = MagicMock(spec=User)
        reply_user.id = 789012
        reply_user.username = "replyuser"

        reply_message = MagicMock(spec=Message)
        reply_message.from_user = reply_user
        reply_message.text = "Test message"

        mock_update.message.reply_to_message = reply_message

        await mom_llm.handle(mock_update, mock_context)

        assert "₹okda" in mock_update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_handle_no_target_message(mock_update, mock_context):
    """Test mom3 handler when target message is None."""
    with (
        patch("src.bot.handlers.mom_llm.dc"),
        patch("src.bot.handlers.mom_llm.util") as mock_util,
        patch("src.bot.handlers.mom_llm.mom_spacy") as mock_mom_spacy,
    ):
        mock_util.paywall_user.return_value = True
        mock_mom_spacy.extract_target_message.return_value = None

        reply_user = MagicMock(spec=User)
        reply_user.id = 789012
        reply_user.username = "replyuser"

        reply_message = MagicMock(spec=Message)
        reply_message.from_user = reply_user
        reply_message.text = None
        reply_message.caption = None

        mock_update.message.reply_to_message = reply_message

        await mom_llm.handle(mock_update, mock_context)

        assert not mock_update.message.reply_text.called


@pytest.mark.asyncio
async def test_handle_success_with_reply_to_message(mock_update, mock_context):
    """Test mom3 handler success with reply to message."""
    with (
        patch("src.bot.handlers.mom_llm.dc"),
        patch("src.bot.handlers.mom_llm.util") as mock_util,
        patch("src.bot.handlers.mom_llm.mom_spacy") as mock_mom_spacy,
        patch("src.bot.handlers.mom_llm.ai.get_openai_client") as mock_get_client,
        patch("src.bot.handlers.mom_llm.open") as mock_open,
    ):
        mock_util.paywall_user.return_value = True
        mock_mom_spacy.extract_target_message.return_value = "Test message"

        mock_open.return_value.__enter__.return_value.read.return_value = "Instructions"

        reply_user = MagicMock(spec=User)
        reply_user.id = 789012
        reply_user.username = "replyuser"

        reply_message = MagicMock(spec=Message)
        reply_message.from_user = reply_user
        reply_message.text = "Test message"
        reply_message.reply_text = AsyncMock()

        mock_update.message.reply_to_message = reply_message

        mock_llm_client = MagicMock()
        mock_llm_response = ai.LLMResponse(
            text="1. Joke 1\n2. Joke 2\n3. Joke 3\n4. Joke 4", provider="openai"
        )
        mock_llm_client.generate = AsyncMock(return_value=mock_llm_response)
        mock_get_client.return_value = mock_llm_client

        await mom_llm.handle(mock_update, mock_context)

        assert reply_message.reply_text.called


@pytest.mark.asyncio
async def test_handle_success_without_reply_to_message(mock_update, mock_context):
    """Test mom3 handler success without reply to message."""
    with (
        patch("src.bot.handlers.mom_llm.dc"),
        patch("src.bot.handlers.mom_llm.util") as mock_util,
        patch("src.bot.handlers.mom_llm.mom_spacy") as mock_mom_spacy,
        patch("src.bot.handlers.mom_llm.ai.get_openai_client") as mock_get_client,
        patch("src.bot.handlers.mom_llm.open") as mock_open,
    ):
        mock_util.paywall_user.return_value = True
        mock_mom_spacy.extract_target_message.return_value = "Test message from caption"

        mock_open.return_value.__enter__.return_value.read.return_value = "Instructions"

        mock_update.message.reply_to_message = None

        mock_llm_client = MagicMock()
        mock_llm_response = ai.LLMResponse(
            text="1. Joke 1\n2. Joke 2\n3. Joke 3\n4. Joke 4", provider="openai"
        )
        mock_llm_client.generate = AsyncMock(return_value=mock_llm_response)
        mock_get_client.return_value = mock_llm_client

        sent_message = MagicMock()
        sent_message.edit_text = AsyncMock()
        mock_update.message.reply_text = AsyncMock(return_value=sent_message)

        await mom_llm.handle(mock_update, mock_context)

        assert sent_message.edit_text.called


@pytest.mark.asyncio
async def test_handle_parses_numbered_jokes(mock_update, mock_context):
    """Test mom3 handler parses numbered jokes correctly."""
    with (
        patch("src.bot.handlers.mom_llm.dc"),
        patch("src.bot.handlers.mom_llm.util") as mock_util,
        patch("src.bot.handlers.mom_llm.mom_spacy") as mock_mom_spacy,
        patch("src.bot.handlers.mom_llm.ai.get_openai_client") as mock_get_client,
        patch("src.bot.handlers.mom_llm.open") as mock_open,
    ):
        mock_util.paywall_user.return_value = True
        mock_mom_spacy.extract_target_message.return_value = "Test message"

        mock_open.return_value.__enter__.return_value.read.return_value = "Instructions"

        reply_user = MagicMock(spec=User)
        reply_user.id = 789012
        reply_user.username = "replyuser"

        reply_message = MagicMock(spec=Message)
        reply_message.from_user = reply_user
        reply_message.text = "Test message"

        mock_update.message.reply_to_message = reply_message

        mock_llm_client = MagicMock()
        mock_llm_response1 = ai.LLMResponse(
            text="1. First joke\n2. Second joke\n3. Third joke\n4. Fourth joke", provider="openai"
        )
        mock_llm_response2 = ai.LLMResponse(text="First joke", provider="openai")
        mock_llm_client.generate = AsyncMock(side_effect=[mock_llm_response1, mock_llm_response2])
        mock_get_client.return_value = mock_llm_client

        sent_message = MagicMock()
        sent_message.edit_text = AsyncMock()
        mock_update.message.reply_to_message.reply_text = AsyncMock(return_value=sent_message)

        await mom_llm.handle(mock_update, mock_context)

        assert sent_message.edit_text.call_count >= 2  # At least "curating" and final joke


@pytest.mark.asyncio
async def test_handle_fallback_parsing(mock_update, mock_context):
    """Test mom3 handler falls back to parsing by double newlines."""
    with (
        patch("src.bot.handlers.mom_llm.dc"),
        patch("src.bot.handlers.mom_llm.util") as mock_util,
        patch("src.bot.handlers.mom_llm.mom_spacy") as mock_mom_spacy,
        patch("src.bot.handlers.mom_llm.ai.get_openai_client") as mock_get_client,
        patch("src.bot.handlers.mom_llm.open") as mock_open,
    ):
        mock_util.paywall_user.return_value = True
        mock_mom_spacy.extract_target_message.return_value = "Test message"

        mock_open.return_value.__enter__.return_value.read.return_value = "Instructions"

        reply_user = MagicMock(spec=User)
        reply_user.id = 789012
        reply_user.username = "replyuser"

        reply_message = MagicMock(spec=Message)
        reply_message.from_user = reply_user
        reply_message.text = "Test message"

        mock_update.message.reply_to_message = reply_message

        mock_llm_client = MagicMock()
        mock_llm_response1 = ai.LLMResponse(
            text="Joke 1\n\nJoke 2\n\nJoke 3\n\nJoke 4", provider="openai"
        )
        mock_llm_response2 = ai.LLMResponse(text="Joke 1", provider="openai")
        mock_llm_client.generate = AsyncMock(side_effect=[mock_llm_response1, mock_llm_response2])
        mock_get_client.return_value = mock_llm_client

        sent_message = MagicMock()
        sent_message.edit_text = AsyncMock()
        mock_update.message.reply_to_message.reply_text = AsyncMock(return_value=sent_message)

        await mom_llm.handle(mock_update, mock_context)

        assert sent_message.edit_text.called


@pytest.mark.asyncio
async def test_handle_uses_entire_response_as_fallback(mock_update, mock_context):
    """Test mom3 handler uses entire response if parsing fails."""
    with (
        patch("src.bot.handlers.mom_llm.dc"),
        patch("src.bot.handlers.mom_llm.util") as mock_util,
        patch("src.bot.handlers.mom_llm.mom_spacy") as mock_mom_spacy,
        patch("src.bot.handlers.mom_llm.ai.get_openai_client") as mock_get_client,
        patch("src.bot.handlers.mom_llm.open") as mock_open,
    ):
        mock_util.paywall_user.return_value = True
        mock_mom_spacy.extract_target_message.return_value = "Test message"

        mock_open.return_value.__enter__.return_value.read.return_value = "Instructions"

        reply_user = MagicMock(spec=User)
        reply_user.id = 789012
        reply_user.username = "replyuser"

        reply_message = MagicMock(spec=Message)
        reply_message.from_user = reply_user
        reply_message.text = "Test message"

        mock_update.message.reply_to_message = reply_message

        mock_llm_client = MagicMock()
        mock_llm_response1 = ai.LLMResponse(text="Single joke without numbering", provider="openai")
        mock_llm_response2 = ai.LLMResponse(text="Single joke without numbering", provider="openai")
        mock_llm_client.generate = AsyncMock(side_effect=[mock_llm_response1, mock_llm_response2])
        mock_get_client.return_value = mock_llm_client

        sent_message = MagicMock()
        sent_message.edit_text = AsyncMock()
        mock_update.message.reply_to_message.reply_text = AsyncMock(return_value=sent_message)

        await mom_llm.handle(mock_update, mock_context)

        assert sent_message.edit_text.called


@pytest.mark.asyncio
async def test_handle_picks_funniest_joke(mock_update, mock_context):
    """Test mom3 handler asks LLM to pick the funniest joke."""
    with (
        patch("src.bot.handlers.mom_llm.dc"),
        patch("src.bot.handlers.mom_llm.util") as mock_util,
        patch("src.bot.handlers.mom_llm.mom_spacy") as mock_mom_spacy,
        patch("src.bot.handlers.mom_llm.ai.get_openai_client") as mock_get_client,
        patch("src.bot.handlers.mom_llm.open") as mock_open,
    ):
        mock_util.paywall_user.return_value = True
        mock_mom_spacy.extract_target_message.return_value = "Test message"

        mock_open.return_value.__enter__.return_value.read.return_value = "Instructions"

        reply_user = MagicMock(spec=User)
        reply_user.id = 789012
        reply_user.username = "replyuser"

        reply_message = MagicMock(spec=Message)
        reply_message.from_user = reply_user
        reply_message.text = "Test message"

        mock_update.message.reply_to_message = reply_message

        mock_llm_client = MagicMock()
        mock_llm_response1 = ai.LLMResponse(
            text="1. Joke 1\n2. Joke 2\n3. Joke 3\n4. Joke 4", provider="openai"
        )
        mock_llm_response2 = ai.LLMResponse(text="Joke 2", provider="openai")
        mock_llm_client.generate = AsyncMock(side_effect=[mock_llm_response1, mock_llm_response2])
        mock_get_client.return_value = mock_llm_client

        sent_message = MagicMock()
        sent_message.edit_text = AsyncMock()
        mock_update.message.reply_to_message.reply_text = AsyncMock(return_value=sent_message)

        await mom_llm.handle(mock_update, mock_context)

        assert mock_llm_client.generate.call_count == 2
        assert sent_message.edit_text.call_count >= 2
