from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Chat, Message, PhotoSize, Update, User
from telegram.ext import ContextTypes

from src.bot.handlers import ai


@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.effective_user = MagicMock(spec=User)
    update.effective_chat = MagicMock(spec=Chat)
    return update


@pytest.fixture
def mock_context():
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    return context


@pytest.fixture
def mock_llm_client():
    client = AsyncMock()
    client.generate_streaming = AsyncMock(return_value="AI response text")
    return client


@pytest.mark.asyncio
@patch("src.bot.handlers.ai.util.paywall_user")
async def test_handle_insufficient_rokda(mock_paywall, mock_update, mock_context):
    """Test handler with insufficient rokda"""
    mock_paywall.return_value = False
    mock_update.effective_user.id = 123
    mock_context.args = ["test", "question"]

    await ai.handle(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args
    assert "don't have enough" in call_args[0][0]


@pytest.mark.asyncio
@patch("src.bot.handlers.ai.Group")
@patch("src.bot.handlers.ai.util.paywall_user")
async def test_handle_command_disabled_for_group(
    mock_paywall, mock_group_class, mock_update, mock_context
):
    """Test handler when command is disabled for group"""
    mock_paywall.return_value = True
    mock_update.effective_user.id = 123
    mock_update.effective_chat.id = 456
    mock_context.args = ["test", "question"]

    mock_group = MagicMock()
    mock_group.metadata = {}
    mock_group_class.get_by_id.return_value = mock_group

    await ai.handle(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args
    assert "not enabled" in call_args[0][0]


@pytest.mark.asyncio
@patch("src.bot.handlers.ai.Group")
@patch("src.bot.handlers.ai.util.paywall_user")
async def test_handle_no_message_provided(
    mock_paywall, mock_group_class, mock_update, mock_context
):
    """Test handler with no message text or image"""
    mock_paywall.return_value = True
    mock_update.effective_user.id = 123
    mock_update.effective_chat.id = 456

    mock_group = MagicMock()
    mock_group.metadata = {"enabled_commands": ["ai"]}
    mock_group_class.get_by_id.return_value = mock_group
    mock_context.args = None
    mock_update.message.reply_to_message = None
    mock_update.message.photo = None

    await ai.handle(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args
    assert "Please provide a question" in call_args[0][0]


@pytest.mark.asyncio
@patch("src.bot.handlers.ai.ai")
@patch("src.bot.handlers.ai.Group")
@patch("src.bot.handlers.ai.util.paywall_user")
async def test_handle_with_args(
    mock_paywall, mock_group_class, mock_ai_module, mock_update, mock_context, mock_llm_client
):
    """Test handler with command args"""
    mock_paywall.return_value = True
    mock_update.effective_user.id = 123
    mock_update.effective_chat.id = 456

    mock_group = MagicMock()
    mock_group.metadata = {"enabled_commands": ["ai"]}
    mock_group_class.get_by_id.return_value = mock_group

    mock_context.args = ["what", "is", "AI?"]
    mock_update.message.reply_to_message = None
    mock_update.message.photo = None

    mock_ai_module.get_default_client.return_value = mock_llm_client

    sent_message = AsyncMock()
    sent_message.edit_text = AsyncMock()
    mock_update.message.reply_text = AsyncMock(return_value=sent_message)

    await ai.handle(mock_update, mock_context)

    mock_llm_client.generate_streaming.assert_called_once()


@pytest.mark.asyncio
@patch("src.bot.handlers.ai.ai")
@patch("src.bot.handlers.ai.Group")
@patch("src.bot.handlers.ai.util.paywall_user")
async def test_handle_markdown_parse_error(
    mock_paywall, mock_group_class, mock_ai_module, mock_update, mock_context, mock_llm_client
):
    """Test handler when markdown parsing fails"""
    mock_paywall.return_value = True
    mock_update.effective_user.id = 123
    mock_update.effective_chat.id = 456

    mock_group = MagicMock()
    mock_group.metadata = {"enabled_commands": ["ai"]}
    mock_group_class.get_by_id.return_value = mock_group

    mock_context.args = ["test", "question"]
    mock_update.message.reply_to_message = None
    mock_update.message.photo = None

    mock_ai_module.get_default_client.return_value = mock_llm_client
    mock_llm_client.generate_streaming.return_value = "**Response** with invalid markdown"

    sent_message = AsyncMock()
    sent_message.edit_text = AsyncMock(side_effect=[Exception("Markdown error"), None])
    mock_update.message.reply_text = AsyncMock(return_value=sent_message)

    await ai.handle(mock_update, mock_context)

    # Should edit twice - once with markdown, once without
    assert sent_message.edit_text.call_count == 2


@pytest.mark.asyncio
@patch("src.bot.handlers.ai.ai")
@patch("src.bot.handlers.ai.Group")
@patch("src.bot.handlers.ai.util.paywall_user")
async def test_handle_with_image_bytes(
    mock_paywall, mock_group_class, mock_ai_module, mock_update, mock_context, mock_llm_client
):
    """Test that image bytes are correctly converted"""
    mock_paywall.return_value = True
    mock_update.effective_user.id = 123
    mock_update.effective_chat.id = 456

    mock_group = MagicMock()
    mock_group.metadata = {"enabled_commands": ["ai"]}
    mock_group_class.get_by_id.return_value = mock_group

    mock_context.args = None
    mock_update.message.reply_to_message = None

    mock_photo_size = MagicMock(spec=PhotoSize)
    mock_photo_file = AsyncMock()
    mock_photo_file.download_as_bytearray = AsyncMock(return_value=b"image_bytes")
    mock_photo_size.get_file.return_value = mock_photo_file
    mock_update.message.photo = [mock_photo_size]
    mock_update.message.caption = None

    mock_ai_module.get_default_client.return_value = mock_llm_client

    sent_message = AsyncMock()
    sent_message.edit_text = AsyncMock()
    mock_update.message.reply_text = AsyncMock(return_value=sent_message)

    await ai.handle(mock_update, mock_context)

    call_args = mock_llm_client.generate_streaming.call_args
    assert isinstance(call_args.kwargs["image_bytes"], bytes)


@pytest.mark.asyncio
@patch("src.bot.handlers.ai.ai")
@patch("src.bot.handlers.ai.Group")
@patch("src.bot.handlers.ai.util.paywall_user")
async def test_handle_streaming_updates(
    mock_paywall, mock_group_class, mock_ai_module, mock_update, mock_context, mock_llm_client
):
    """Test that streaming updates are sent"""
    mock_paywall.return_value = True
    mock_update.effective_user.id = 123
    mock_update.effective_chat.id = 456

    mock_group = MagicMock()
    mock_group.metadata = {"enabled_commands": ["ai"]}
    mock_group_class.get_by_id.return_value = mock_group

    mock_context.args = ["test", "question"]
    mock_update.message.reply_to_message = None
    mock_update.message.photo = None

    mock_ai_module.get_default_client.return_value = mock_llm_client

    sent_message = AsyncMock()
    sent_message.edit_text = AsyncMock()
    mock_update.message.reply_text = AsyncMock(return_value=sent_message)

    await ai.handle(mock_update, mock_context)

    # Verify streaming callback was used
    assert mock_llm_client.generate_streaming.called


@pytest.mark.asyncio
@patch("src.bot.handlers.ai.ai")
@patch("src.bot.handlers.ai.Group")
@patch("src.bot.handlers.ai.util.paywall_user")
async def test_handle_command_logging(
    mock_paywall, mock_group_class, mock_ai_module, mock_update, mock_context, mock_llm_client
):
    """Test that command usage is logged"""
    mock_paywall.return_value = True
    mock_update.effective_user.id = 123
    mock_update.effective_chat.id = 456

    mock_group = MagicMock()
    mock_group.metadata = {"enabled_commands": ["ai"]}
    mock_group_class.get_by_id.return_value = mock_group

    mock_context.args = ["test", "question"]
    mock_update.message.reply_to_message = None
    mock_update.message.photo = None

    mock_ai_module.get_default_client.return_value = mock_llm_client

    sent_message = AsyncMock()
    sent_message.edit_text = AsyncMock()
    mock_update.message.reply_text = AsyncMock(return_value=sent_message)

    with patch("src.bot.handlers.ai.dc.log_command_usage") as mock_log:
        await ai.handle(mock_update, mock_context)
        mock_log.assert_called_once_with("ai", mock_update)
