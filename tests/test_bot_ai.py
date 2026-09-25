from datetime import datetime, timedelta
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
@patch("src.bot.handlers.ai.Group")
@patch("src.bot.handlers.ai.util.paywall_user")
async def test_handle_insufficient_rokda(mock_paywall, mock_group_class, mock_update, mock_context):
    """Test handler with insufficient rokda"""
    mock_paywall.return_value = False
    mock_update.effective_user.id = 123
    mock_context.args = ["test", "question"]
    mock_update.message.reply_to_message = None
    mock_update.message.photo = None
    mock_update.message.caption = None

    mock_group = MagicMock()
    mock_group.metadata = {"enabled_commands": ["ai"]}
    mock_group_class.get_by_id.return_value = mock_group

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
    mock_update.message.caption = None

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
async def test_handle_question_param(
    mock_paywall, mock_group_class, mock_ai_module, mock_update, mock_context, mock_llm_client
):
    """The question param is used when there are no command args (the mention path)"""
    mock_paywall.return_value = True
    mock_update.effective_user.id = 123
    mock_update.effective_chat.id = 456
    mock_update.message.from_user.username = "arkits"

    mock_group = MagicMock()
    mock_group.metadata = {"enabled_commands": ["ai"]}
    mock_group_class.get_by_id.return_value = mock_group

    mock_context.args = None
    mock_update.message.reply_to_message = None
    mock_update.message.photo = None
    mock_update.message.caption = None

    mock_ai_module.get_default_client.return_value = mock_llm_client

    sent_message = AsyncMock()
    sent_message.edit_text = AsyncMock()
    mock_update.message.reply_text = AsyncMock(return_value=sent_message)

    await ai.handle(mock_update, mock_context, question="how much is 10000 divided by 12")

    messages = mock_llm_client.generate_streaming.call_args.kwargs["messages"]
    assert messages[-1]["content"] == "@arkits: how much is 10000 divided by 12"


@pytest.mark.asyncio
@patch("src.bot.handlers.ai.Group")
@patch("src.bot.handlers.ai.util.paywall_user")
async def test_handle_quiet_skips_paywall_reply(
    mock_paywall, mock_group_class, mock_update, mock_context
):
    """quiet=True suppresses the not-enough-rokda reply"""
    mock_paywall.return_value = False
    mock_update.effective_user.id = 123
    mock_update.effective_chat.id = 456
    mock_context.args = None
    mock_update.message.reply_to_message = None
    mock_update.message.photo = None
    mock_update.message.caption = None

    mock_group = MagicMock()
    mock_group.metadata = {"enabled_commands": ["ai"]}
    mock_group_class.get_by_id.return_value = mock_group

    await ai.handle(mock_update, mock_context, question="hello", quiet=True)

    mock_paywall.assert_called_once()
    assert not mock_update.message.reply_text.called


@pytest.mark.asyncio
@patch("src.bot.handlers.ai.Group")
@patch("src.bot.handlers.ai.util.paywall_user")
async def test_handle_quiet_skips_disabled_group_reply(
    mock_paywall, mock_group_class, mock_update, mock_context
):
    """quiet=True suppresses the command-not-enabled reply"""
    mock_paywall.return_value = True
    mock_update.effective_user.id = 123
    mock_update.effective_chat.id = 456
    mock_context.args = None

    mock_group = MagicMock()
    mock_group.metadata = {}
    mock_group_class.get_by_id.return_value = mock_group

    await ai.handle(mock_update, mock_context, question="hello", quiet=True)

    assert not mock_update.message.reply_text.called


@pytest.mark.asyncio
@patch("src.bot.handlers.ai.Group")
@patch("src.bot.handlers.ai.util.paywall_user")
async def test_handle_quiet_skips_empty_question_reply(
    mock_paywall, mock_group_class, mock_update, mock_context
):
    """quiet=True suppresses the please-provide-a-question reply for a bare mention"""
    mock_paywall.return_value = True
    mock_update.effective_user.id = 123
    mock_update.effective_chat.id = 456
    mock_context.args = None
    mock_update.message.reply_to_message = None
    mock_update.message.photo = None
    mock_update.message.caption = None

    mock_group = MagicMock()
    mock_group.metadata = {"enabled_commands": ["ai"]}
    mock_group_class.get_by_id.return_value = mock_group

    await ai.handle(mock_update, mock_context, question=None, quiet=True)

    assert not mock_update.message.reply_text.called


@pytest.mark.asyncio
@patch("src.bot.handlers.ai.ai")
@patch("src.bot.handlers.ai.Group")
@patch("src.bot.handlers.ai.util.paywall_user")
async def test_handle_reply_without_args(
    mock_paywall, mock_group_class, mock_ai_module, mock_update, mock_context, mock_llm_client
):
    """Bare `/ai` replying to a text message should use the replied-to message as the question"""
    mock_paywall.return_value = True
    mock_update.effective_user.id = 123
    mock_update.effective_chat.id = 456

    mock_group = MagicMock()
    mock_group.metadata = {"enabled_commands": ["ai"]}
    mock_group_class.get_by_id.return_value = mock_group

    mock_context.args = None
    mock_update.message.photo = None
    mock_update.message.caption = None

    reply_user = MagicMock(spec=User)
    reply_user.username = "minji"
    reply_message = MagicMock(spec=Message)
    reply_message.text = "What's the consensus on tongue cleaners?"
    reply_message.caption = None
    reply_message.photo = None
    reply_message.from_user = reply_user
    mock_update.message.reply_to_message = reply_message

    mock_ai_module.get_default_client.return_value = mock_llm_client

    sent_message = AsyncMock()
    sent_message.edit_text = AsyncMock()
    mock_update.message.reply_text = AsyncMock(return_value=sent_message)

    await ai.handle(mock_update, mock_context)

    mock_llm_client.generate_streaming.assert_called_once()
    messages = mock_llm_client.generate_streaming.call_args.kwargs["messages"]
    assert messages[-1]["content"] == "@minji: What's the consensus on tongue cleaners?"


@pytest.mark.asyncio
@patch("src.bot.handlers.ai.ai")
@patch("src.bot.handlers.ai.Group")
@patch("src.bot.handlers.ai.util.paywall_user")
async def test_handle_reply_with_args(
    mock_paywall, mock_group_class, mock_ai_module, mock_update, mock_context, mock_llm_client
):
    """`/ai <question>` replying to a message should include both the reply and the question"""
    mock_paywall.return_value = True
    mock_update.effective_user.id = 123
    mock_update.effective_chat.id = 456

    mock_group = MagicMock()
    mock_group.metadata = {"enabled_commands": ["ai"]}
    mock_group_class.get_by_id.return_value = mock_group

    mock_context.args = ["is", "this", "true?"]
    mock_update.message.photo = None
    mock_update.message.caption = None
    mock_update.message.from_user.username = "arkits"

    reply_user = MagicMock(spec=User)
    reply_user.username = "minji"
    reply_message = MagicMock(spec=Message)
    reply_message.text = "Tongue cleaners are useless"
    reply_message.caption = None
    reply_message.photo = None
    reply_message.from_user = reply_user
    mock_update.message.reply_to_message = reply_message

    mock_ai_module.get_default_client.return_value = mock_llm_client

    sent_message = AsyncMock()
    sent_message.edit_text = AsyncMock()
    mock_update.message.reply_text = AsyncMock(return_value=sent_message)

    await ai.handle(mock_update, mock_context)

    mock_llm_client.generate_streaming.assert_called_once()
    messages = mock_llm_client.generate_streaming.call_args.kwargs["messages"]
    assert messages[-1]["content"] == (
        "@minji: Tongue cleaners are useless\n\n@arkits: is this true?"
    )


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


@patch("src.bot.handlers.ai.CommandUsage")
@patch("src.db.Group")
def test_build_conversation_messages_without_clear(mock_group_class, mock_command_usage):
    """Test building conversation messages without AI thread cleared."""
    # Setup mock group without clear timestamp
    mock_group = MagicMock()
    mock_group.metadata = {}
    mock_group_class.get_by_id.return_value = mock_group

    # Create mock command usages
    usage1 = MagicMock()
    usage1.executed_at = datetime.now() - timedelta(hours=2)
    usage1.metadata = {"user_message": "Message 1", "bot_response": "Response 1"}

    usage2 = MagicMock()
    usage2.executed_at = datetime.now() - timedelta(hours=1)
    usage2.metadata = {"user_message": "Message 2", "bot_response": "Response 2"}

    mock_command_usage.select.return_value.where.return_value.where.return_value.where.return_value.order_by.return_value.limit.return_value = [
        usage2,
        usage1,
    ]

    # Build messages
    result = ai._build_ai_conversation_messages(
        "123", limit=50, current_user_message="Current message"
    )

    # Should include all messages
    assert len(result) == 5  # user1 + assistant1 + user2 + assistant2 + current message
    assert result[0]["role"] == "user"
    assert result[0]["content"] == "Message 1"
    assert result[1]["role"] == "assistant"
    assert result[1]["content"] == "Response 1"
    assert result[2]["role"] == "user"
    assert result[2]["content"] == "Message 2"
    assert result[3]["role"] == "assistant"
    assert result[3]["content"] == "Response 2"
    assert result[4]["role"] == "user"
    assert result[4]["content"] == "Current message"


@patch("src.bot.handlers.ai.CommandUsage")
@patch("src.db.Group")
def test_build_conversation_messages_empty_after_clear(mock_group_class, mock_command_usage):
    """Test building conversation messages when thread was cleared and there are no new messages."""
    # Setup mock group with clear timestamp
    mock_group = MagicMock()
    clear_time = datetime.now() - timedelta(hours=1)
    mock_group.metadata = {"ai_thread_cleared_at": clear_time.isoformat()}
    mock_group_class.get_by_id.return_value = mock_group

    # No command usages after the clear timestamp
    mock_command_usage.select.return_value.where.return_value.where.return_value.where.return_value.where.return_value.order_by.return_value.limit.return_value = []

    # Build messages
    result = ai._build_ai_conversation_messages(
        "123", limit=50, current_user_message="Current message"
    )

    # Should only include current message
    assert len(result) == 1
    assert result[0]["role"] == "user"
    assert result[0]["content"] == "Current message"


def _enabled_group(mock_group_class):
    mock_group = MagicMock()
    mock_group.metadata = {"enabled_commands": ["ai"]}
    mock_group_class.get_by_id.return_value = mock_group


def _plain_message(mock_update, mock_context, args):
    mock_update.effective_user.id = 123
    mock_update.effective_chat.id = 456
    mock_update.message.chat.id = 456
    mock_update.message.chat.type = "private"
    mock_update.message.message_id = 789
    mock_update.message.from_user.username = "arkits"
    mock_context.args = args
    mock_update.message.reply_to_message = None
    mock_update.message.photo = None
    mock_update.message.caption = None
    sent_message = AsyncMock()
    mock_update.message.reply_text = AsyncMock(return_value=sent_message)
    return sent_message


@pytest.mark.asyncio
@patch("src.bot.handlers.ai.Group")
@patch("src.bot.handlers.ai.util.paywall_user")
async def test_handle_disabled_group_does_not_charge(
    mock_paywall, mock_group_class, mock_update, mock_context
):
    """Users aren't charged when the command is disabled for the group"""
    _plain_message(mock_update, mock_context, ["hello"])
    mock_group_class.get_by_id.return_value = MagicMock(metadata={})

    await ai.handle(mock_update, mock_context)

    mock_paywall.assert_not_called()


@pytest.mark.asyncio
@patch("src.bot.handlers.ai.Group")
@patch("src.bot.handlers.ai.util.paywall_user")
async def test_handle_empty_question_does_not_charge(
    mock_paywall, mock_group_class, mock_update, mock_context
):
    """Users aren't charged for a bare /ai with nothing to answer"""
    _plain_message(mock_update, mock_context, None)
    _enabled_group(mock_group_class)

    await ai.handle(mock_update, mock_context)

    mock_paywall.assert_not_called()
    assert "Please provide a question" in mock_update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
@patch("src.bot.handlers.ai.Group")
@patch("src.bot.handlers.ai.util.paywall_user")
async def test_handle_unknown_group_is_disabled(
    mock_paywall, mock_group_class, mock_update, mock_context
):
    """A chat with no Group row (eg. a DM) is treated as disabled, not as an error"""
    from peewee import DoesNotExist

    _plain_message(mock_update, mock_context, ["hello"])
    mock_group_class.get_by_id.side_effect = DoesNotExist()

    await ai.handle(mock_update, mock_context)

    mock_paywall.assert_not_called()
    assert "not enabled" in mock_update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
@patch("src.bot.handlers.ai.Group")
@patch("src.bot.handlers.ai.util.paywall_user")
async def test_handle_group_lookup_error_replies(
    mock_paywall, mock_group_class, mock_update, mock_context
):
    """An error checking permissions tells the user instead of failing silently"""
    _plain_message(mock_update, mock_context, ["hello"])
    mock_group_class.get_by_id.side_effect = RuntimeError("db down")

    await ai.handle(mock_update, mock_context)

    mock_paywall.assert_not_called()
    assert "Something went wrong" in mock_update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
@patch("src.bot.handlers.ai.ai")
@patch("src.bot.handlers.ai.Group")
@patch("src.bot.handlers.ai.util.paywall_user")
async def test_handle_caption_strips_command_with_bot_username(
    mock_paywall, mock_group_class, mock_ai_module, mock_update, mock_context, mock_llm_client
):
    """`/ai@botname question` in a caption only sends the question"""
    mock_paywall.return_value = True
    _plain_message(mock_update, mock_context, None)
    _enabled_group(mock_group_class)
    mock_update.message.caption = "/ai@chaddi_bot what is this?"
    mock_ai_module.get_default_client.return_value = mock_llm_client

    await ai.handle(mock_update, mock_context)

    messages = mock_llm_client.generate_streaming.call_args.kwargs["messages"]
    assert messages[-1]["content"] == "@arkits: what is this?"


@pytest.mark.asyncio
@patch("src.bot.handlers.ai.ai")
@patch("src.bot.handlers.ai.Group")
@patch("src.bot.handlers.ai.util.paywall_user")
async def test_handle_long_response_is_split(
    mock_paywall, mock_group_class, mock_ai_module, mock_update, mock_context, mock_llm_client
):
    """Responses over Telegram's limit spill over into follow-up replies"""
    mock_paywall.return_value = True
    sent_message = _plain_message(mock_update, mock_context, ["long", "please"])
    _enabled_group(mock_group_class)
    mock_ai_module.get_default_client.return_value = mock_llm_client
    mock_llm_client.generate_streaming.return_value = ("word " * 1000 + "\n") * 2

    await ai.handle(mock_update, mock_context)

    edited = sent_message.edit_text.call_args[0][0]
    followups = [c[0][0] for c in sent_message.reply_text.call_args_list]
    assert len(edited) <= ai.MAX_MESSAGE_LENGTH
    assert followups
    assert all(len(f) <= ai.MAX_MESSAGE_LENGTH for f in followups)
    assert (edited + " " + " ".join(followups)).split() == ["word"] * 2000


@pytest.mark.asyncio
@patch("src.bot.handlers.ai.ai")
@patch("src.bot.handlers.ai.Group")
@patch("src.bot.handlers.ai.util.paywall_user")
async def test_handle_saves_conversation_to_logged_usage(
    mock_paywall, mock_group_class, mock_ai_module, mock_update, mock_context, mock_llm_client
):
    """The conversation is saved to the CommandUsage created for this request"""
    mock_paywall.return_value = True
    _plain_message(mock_update, mock_context, ["hi"])
    _enabled_group(mock_group_class)
    mock_ai_module.get_default_client.return_value = mock_llm_client

    usage = MagicMock()
    usage.metadata = None
    with patch("src.bot.handlers.ai.dc.log_command_usage", return_value=usage):
        await ai.handle(mock_update, mock_context)

    assert usage.metadata == {"user_message": "@arkits: hi", "bot_response": "AI response text"}
    usage.save.assert_called_once()


@pytest.mark.asyncio
@patch("src.bot.handlers.ai.ai")
@patch("src.bot.handlers.ai.Group")
@patch("src.bot.handlers.ai.util.paywall_user")
async def test_handle_passes_chat_history_tool(
    mock_paywall, mock_group_class, mock_ai_module, mock_update, mock_context, mock_llm_client
):
    """The model gets a chat history tool scoped to the current chat"""
    mock_paywall.return_value = True
    _plain_message(mock_update, mock_context, ["what", "happened?"])
    _enabled_group(mock_group_class)
    mock_ai_module.get_default_client.return_value = mock_llm_client

    await ai.handle(mock_update, mock_context)

    tools = mock_llm_client.generate_streaming.call_args.kwargs["tools"]
    assert len(tools) == 1
    assert mock_ai_module.LLMTool.call_args.kwargs["name"] == "get_chat_history"


def test_system_prompt_only_advertises_web_search_when_available():
    with_search = MagicMock(has_web_search=True, provider="openrouter")
    without_search = MagicMock(has_web_search=False, provider="openai")

    assert "web search" in ai._build_system_prompt(with_search, 1)
    assert "web search" not in ai._build_system_prompt(without_search, 1)


def test_system_prompt_only_mentions_tool_when_supported():
    assert "get_chat_history" in ai._build_system_prompt(MagicMock(provider="openrouter"), 42)
    assert "#42" in ai._build_system_prompt(MagicMock(provider="openrouter"), 42)
    assert "get_chat_history" not in ai._build_system_prompt(MagicMock(provider="gemini"), 42)


def _logged_message(message_id, text, username, reply_to=None, minute=0):
    message = MagicMock()
    message.message_id = str(message_id)
    message.text = text
    message.time_sent = datetime(2026, 9, 24, 18, minute)
    message.from_bakchod.username = username
    update = {"message": {"message_id": message_id}}
    if reply_to is not None:
        update["message"]["reply_to_message"] = {"message_id": reply_to}
    message.update = update
    return message


@patch("src.bot.handlers.ai.message_dao")
def test_chat_history_tool_formats_messages(mock_message_dao):
    mock_message_dao.get_chat_messages.return_value = [
        _logged_message(10, "anyone up for chai?", "minji", minute=1),
        _logged_message(11, "always", "arkits", reply_to=10, minute=2),
    ]

    tool = ai._build_chat_history_tool(456)
    result = tool.handler(limit=5, search="chai")

    mock_message_dao.get_chat_messages.assert_called_once_with(
        456, limit=5, before_message_id=None, search="chai"
    )
    assert result == (
        "[#10 Sep 24 18:01] @minji: anyone up for chai?\n"
        "[#11 Sep 24 18:02] @arkits (replying to #10): always"
    )


@patch("src.bot.handlers.ai.message_dao")
def test_chat_history_tool_clamps_limit_and_truncates(mock_message_dao):
    mock_message_dao.get_chat_messages.return_value = [
        _logged_message(10, "x" * 1000, "minji"),
    ]

    tool = ai._build_chat_history_tool(456)
    result = tool.handler(limit=10_000, before_message_id=99)

    assert mock_message_dao.get_chat_messages.call_args.kwargs["limit"] == ai.CHAT_HISTORY_MAX_LIMIT
    assert mock_message_dao.get_chat_messages.call_args.kwargs["before_message_id"] == 99
    assert result.endswith("x" * ai.CHAT_HISTORY_MAX_TEXT_LENGTH + "…")


@patch("src.bot.handlers.ai.message_dao")
def test_chat_history_tool_no_messages(mock_message_dao):
    mock_message_dao.get_chat_messages.return_value = []

    assert ai._build_chat_history_tool(456).handler() == "No messages found."


def test_split_message():
    assert ai._split_message("short") == ["short"]
    assert ai._split_message("") == [""]
    assert ai._split_message("aaaa\nbbbb", limit=6) == ["aaaa", "bbbb"]
    assert ai._split_message("aaa bbb ccc", limit=8) == ["aaa bbb", "ccc"]
    assert ai._split_message("abcdefgh", limit=3) == ["abc", "def", "gh"]
