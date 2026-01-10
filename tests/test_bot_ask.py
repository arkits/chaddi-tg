from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Chat, Message, Update, User
from telegram.ext import ContextTypes

from src.bot.handlers import ask
from src.db import Group


@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.from_user = MagicMock(spec=User)
    update.message.from_user.id = 123
    update.effective_user = update.message.from_user
    update.effective_chat = MagicMock(spec=Chat)
    update.effective_chat.id = 456
    return update


@pytest.fixture
def mock_context():
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = ["test", "question"]
    return context


class TestHandle:
    @pytest.mark.anyio
    async def test_handle_insufficient_rokda(self, mock_update, mock_context):
        with patch("src.bot.handlers.ask.dc"), patch("src.bot.handlers.ask.util") as mock_util:
            mock_util.paywall_user.return_value = False

            await ask.handle(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()
            assert "don't have enough" in mock_update.message.reply_text.call_args[0][0]

    @pytest.mark.anyio
    async def test_handle_command_disabled_for_group(self, mock_update, mock_context):
        with (
            patch("src.bot.handlers.ask.dc"),
            patch("src.bot.handlers.ask.util") as mock_util,
            patch.object(Group, "get_by_id") as mock_get_group,
        ):
            mock_util.paywall_user.return_value = True
            mock_group = MagicMock()
            mock_group.metadata = {"enabled_commands": []}
            mock_get_group.return_value = mock_group

            await ask.handle(mock_update, mock_context)

            mock_update.message.reply_text.assert_called()
            assert "not enabled" in mock_update.message.reply_text.call_args[0][0]

    @pytest.mark.anyio
    async def test_handle_no_message_provided(self, mock_update, mock_context):
        with (
            patch("src.bot.handlers.ask.dc"),
            patch("src.bot.handlers.ask.util") as mock_util,
            patch.object(Group, "get_by_id") as mock_get_group,
        ):
            mock_util.paywall_user.return_value = True
            mock_group = MagicMock()
            mock_group.metadata = {"enabled_commands": ["ask"]}
            mock_get_group.return_value = mock_group
            mock_context.args = None
            mock_update.message.reply_to_message = None

            await ask.handle(mock_update, mock_context)

            mock_update.message.reply_text.assert_called()
            assert "provide a question" in mock_update.message.reply_text.call_args[0][0]

    @pytest.mark.anyio
    async def test_handle_with_args(self, mock_update, mock_context):
        mock_update.message.reply_to_message = None
        sent_message = MagicMock()
        sent_message.edit_text = AsyncMock()
        mock_update.message.reply_text = AsyncMock(return_value=sent_message)

        with (
            patch("src.bot.handlers.ask.dc"),
            patch("src.bot.handlers.ask.util") as mock_util,
            patch.object(Group, "get_by_id") as mock_get_group,
            patch("src.bot.handlers.ask.ai") as mock_ai,
        ):
            mock_util.paywall_user.return_value = True
            mock_group = MagicMock()
            mock_group.metadata = {"enabled_commands": ["ask"]}
            mock_get_group.return_value = mock_group

            mock_llm_client = MagicMock()
            mock_llm_client.generate_streaming = AsyncMock(return_value="Test response")
            mock_ai.get_chatgpt_client.return_value = mock_llm_client

            await ask.handle(mock_update, mock_context)

            assert sent_message.edit_text.call_count >= 1

    @pytest.mark.anyio
    async def test_handle_with_reply_to_text_message(self, mock_update, mock_context):
        mock_context.args = None
        reply_msg = MagicMock(spec=Message)
        reply_msg.text = "This is the question"
        reply_msg.caption = None
        mock_update.message.reply_to_message = reply_msg
        sent_message = MagicMock()
        sent_message.edit_text = AsyncMock()
        mock_update.message.reply_text = AsyncMock(return_value=sent_message)

        with (
            patch("src.bot.handlers.ask.dc"),
            patch("src.bot.handlers.ask.util") as mock_util,
            patch.object(Group, "get_by_id") as mock_get_group,
            patch("src.bot.handlers.ask.ai") as mock_ai,
        ):
            mock_util.paywall_user.return_value = True
            mock_group = MagicMock()
            mock_group.metadata = {"enabled_commands": ["ask"]}
            mock_get_group.return_value = mock_group

            mock_llm_client = MagicMock()
            mock_llm_client.generate_streaming = AsyncMock(return_value="Test response")
            mock_ai.get_chatgpt_client.return_value = mock_llm_client

            await ask.handle(mock_update, mock_context)

            assert sent_message.edit_text.call_count >= 1

    @pytest.mark.anyio
    async def test_handle_with_reply_to_caption_message(self, mock_update, mock_context):
        mock_context.args = None
        reply_msg = MagicMock(spec=Message)
        reply_msg.text = None
        reply_msg.caption = "This is the caption"
        mock_update.message.reply_to_message = reply_msg
        sent_message = MagicMock()
        sent_message.edit_text = AsyncMock()
        mock_update.message.reply_text = AsyncMock(return_value=sent_message)

        with (
            patch("src.bot.handlers.ask.dc"),
            patch("src.bot.handlers.ask.util") as mock_util,
            patch.object(Group, "get_by_id") as mock_get_group,
            patch("src.bot.handlers.ask.ai") as mock_ai,
        ):
            mock_util.paywall_user.return_value = True
            mock_group = MagicMock()
            mock_group.metadata = {"enabled_commands": ["ask"]}
            mock_get_group.return_value = mock_group

            mock_llm_client = MagicMock()
            mock_llm_client.generate_streaming = AsyncMock(return_value="Test response")
            mock_ai.get_chatgpt_client.return_value = mock_llm_client

            await ask.handle(mock_update, mock_context)

            assert sent_message.edit_text.call_count >= 1

    @pytest.mark.anyio
    async def test_handle_markdown_parse_error(self, mock_update, mock_context):
        mock_update.message.reply_to_message = None
        sent_message = MagicMock()
        sent_message.edit_text = AsyncMock(side_effect=[Exception("Parse error"), None])
        mock_update.message.reply_text = AsyncMock(return_value=sent_message)

        with (
            patch("src.bot.handlers.ask.dc"),
            patch("src.bot.handlers.ask.util") as mock_util,
            patch.object(Group, "get_by_id") as mock_get_group,
            patch("src.bot.handlers.ask.ai") as mock_ai,
        ):
            mock_util.paywall_user.return_value = True
            mock_group = MagicMock()
            mock_group.metadata = {"enabled_commands": ["ask"]}
            mock_get_group.return_value = mock_group

            mock_llm_client = MagicMock()
            mock_llm_client.generate_streaming = AsyncMock(return_value="Test response")
            mock_ai.get_chatgpt_client.return_value = mock_llm_client

            await ask.handle(mock_update, mock_context)

            assert sent_message.edit_text.call_count >= 1

    @pytest.mark.anyio
    async def test_handle_exception(self, mock_update, mock_context):
        with (
            patch("src.bot.handlers.ask.dc"),
            patch("src.bot.handlers.ask.util") as mock_util,
            patch("src.bot.handlers.ask.logger") as mock_logger,
        ):
            mock_util.paywall_user.return_value = True
            mock_update.message.reply_text = MagicMock(side_effect=Exception("Test error"))

            await ask.handle(mock_update, mock_context)

            mock_logger.error.assert_called()
