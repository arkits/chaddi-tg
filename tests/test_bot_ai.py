from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Chat, Document, Message, PhotoSize, Update, User
from telegram.ext import ContextTypes

from src.bot.handlers import ai
from src.domain.ai import LLMAttachment

SENT_AT = datetime(2026, 9, 24, 18, 5)


def _tg_message(message_id, username, text=None, caption=None):
    """A Telegram message mock with no media, reply or caption unless set."""
    message = MagicMock(spec=Message)
    message.message_id = message_id
    message.date = SENT_AT
    message.text = text
    message.caption = caption
    message.photo = None
    message.document = None
    message.reply_to_message = None
    message.to_dict.return_value = {}
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 1000 + message_id
    message.from_user.username = username
    return message


@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.message = _tg_message(789, "arkits")
    update.message.chat = MagicMock(spec=Chat)
    update.message.chat.id = 456
    update.message.chat.title = "Bakchods"
    update.message.chat.type = "supergroup"
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 123
    update.effective_chat = MagicMock(spec=Chat)
    update.effective_chat.id = 456
    return update


@pytest.fixture
def mock_context():
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = None
    context.bot = MagicMock()
    context.bot.id = 42
    context.bot.username = "chaddi_bot"
    return context


@pytest.fixture
def mock_llm_client():
    client = AsyncMock()
    client.generate_streaming = AsyncMock(return_value="AI response text")
    return client


@pytest.fixture
def sent_message(mock_update):
    sent = AsyncMock()
    sent.message_id = 790
    mock_update.message.reply_text = AsyncMock(return_value=sent)
    return sent


@pytest.fixture
def enabled_group():
    with patch("src.bot.handlers.ai.Group") as mock_group_class:
        mock_group_class.get_by_id.return_value = MagicMock(metadata={"enabled_commands": ["ai"]})
        yield mock_group_class


@pytest.fixture
def paywall():
    with patch("src.bot.handlers.ai.util.paywall_user", return_value=True) as mock_paywall:
        yield mock_paywall


@pytest.fixture
def llm(mock_llm_client):
    """Patch the ai module the handler uses, keeping the real LLMAttachment."""
    with patch("src.bot.handlers.ai.ai") as mock_ai_module:
        mock_ai_module.get_default_client.return_value = mock_llm_client
        mock_ai_module.LLMAttachment = LLMAttachment
        yield mock_ai_module


@pytest.fixture
def no_transcript():
    with patch("src.bot.handlers.ai._build_transcript", return_value=None) as mock_transcript:
        yield mock_transcript


def _prompt(mock_llm_client) -> str:
    messages = mock_llm_client.generate_streaming.call_args.kwargs["messages"]
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    return messages[0]["content"]


def _file_holder(data: bytes):
    """A PhotoSize / Document whose get_file() downloads `data`."""
    telegram_file = AsyncMock()
    telegram_file.download_as_bytearray = AsyncMock(return_value=bytearray(data))
    return AsyncMock(return_value=telegram_file)


def _document(name, mime_type, data=b"", size=None):
    document = MagicMock(spec=Document)
    document.file_name = name
    document.mime_type = mime_type
    document.file_size = len(data) if size is None else size
    document.get_file = _file_holder(data)
    return document


# --- Guards -----------------------------------------------------------------


@pytest.mark.asyncio
async def test_handle_insufficient_rokda(mock_update, mock_context, enabled_group):
    mock_context.args = ["test", "question"]

    with patch("src.bot.handlers.ai.util.paywall_user", return_value=False):
        await ai.handle(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    assert "don't have enough" in mock_update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_handle_command_disabled_for_group(mock_update, mock_context, paywall):
    mock_context.args = ["test", "question"]

    with patch("src.bot.handlers.ai.Group") as mock_group_class:
        mock_group_class.get_by_id.return_value = MagicMock(metadata={})
        await ai.handle(mock_update, mock_context)

    assert "not enabled" in mock_update.message.reply_text.call_args[0][0]
    paywall.assert_not_called()


@pytest.mark.asyncio
async def test_handle_unknown_group_is_disabled(mock_update, mock_context, paywall):
    """A chat with no Group row (eg. a DM) is treated as disabled, not as an error"""
    from peewee import DoesNotExist

    mock_context.args = ["hello"]

    with patch("src.bot.handlers.ai.Group") as mock_group_class:
        mock_group_class.get_by_id.side_effect = DoesNotExist()
        await ai.handle(mock_update, mock_context)

    paywall.assert_not_called()
    assert "not enabled" in mock_update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_handle_group_lookup_error_replies(mock_update, mock_context, paywall):
    """An error checking permissions tells the user instead of failing silently"""
    mock_context.args = ["hello"]

    with patch("src.bot.handlers.ai.Group") as mock_group_class:
        mock_group_class.get_by_id.side_effect = RuntimeError("db down")
        await ai.handle(mock_update, mock_context)

    paywall.assert_not_called()
    assert "Something went wrong" in mock_update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_handle_empty_question_does_not_charge(
    mock_update, mock_context, enabled_group, paywall
):
    """Users aren't charged for a bare /ai with nothing to answer"""
    await ai.handle(mock_update, mock_context)

    paywall.assert_not_called()
    assert "Please provide a question" in mock_update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_handle_bare_reply_to_sticker_has_nothing_to_answer(
    mock_update, mock_context, enabled_group, paywall
):
    mock_update.message.reply_to_message = _tg_message(10, "minji")

    await ai.handle(mock_update, mock_context)

    paywall.assert_not_called()


@pytest.mark.asyncio
async def test_handle_quiet_skips_paywall_reply(mock_update, mock_context, enabled_group):
    with patch("src.bot.handlers.ai.util.paywall_user", return_value=False) as mock_paywall:
        await ai.handle(mock_update, mock_context, question="hello", quiet=True)

    mock_paywall.assert_called_once()
    assert not mock_update.message.reply_text.called


@pytest.mark.asyncio
async def test_handle_quiet_skips_disabled_group_reply(mock_update, mock_context, paywall):
    with patch("src.bot.handlers.ai.Group") as mock_group_class:
        mock_group_class.get_by_id.return_value = MagicMock(metadata={})
        await ai.handle(mock_update, mock_context, question="hello", quiet=True)

    assert not mock_update.message.reply_text.called


@pytest.mark.asyncio
async def test_handle_quiet_skips_empty_question_reply(
    mock_update, mock_context, enabled_group, paywall
):
    await ai.handle(mock_update, mock_context, question=None, quiet=True)

    assert not mock_update.message.reply_text.called


@pytest.mark.asyncio
async def test_handle_command_logging(
    mock_update, mock_context, enabled_group, paywall, llm, sent_message, no_transcript
):
    mock_context.args = ["test", "question"]

    with patch("src.bot.handlers.ai.dc.log_command_usage") as mock_log:
        await ai.handle(mock_update, mock_context)

    mock_log.assert_called_once_with("ai", mock_update)


# --- Prompt -----------------------------------------------------------------


@pytest.mark.asyncio
async def test_handle_with_args(
    mock_update,
    mock_context,
    enabled_group,
    paywall,
    llm,
    mock_llm_client,
    sent_message,
    no_transcript,
):
    mock_context.args = ["what", "is", "AI?"]

    await ai.handle(mock_update, mock_context)

    assert _prompt(mock_llm_client) == (
        "<request>\n[#789 Thu Sep 24 18:05] @arkits: what is AI?\n</request>"
    )
    kwargs = mock_llm_client.generate_streaming.call_args.kwargs
    assert kwargs["attachments"] == []
    assert '"Bakchods"' in kwargs["system_prompt"]


@pytest.mark.asyncio
async def test_handle_question_param(
    mock_update,
    mock_context,
    enabled_group,
    paywall,
    llm,
    mock_llm_client,
    sent_message,
    no_transcript,
):
    """The question param is used when there are no command args (the mention path)"""
    await ai.handle(mock_update, mock_context, question="how much is 10000 divided by 12")

    assert "@arkits: how much is 10000 divided by 12" in _prompt(mock_llm_client)


@pytest.mark.asyncio
async def test_handle_reply_without_args(
    mock_update,
    mock_context,
    enabled_group,
    paywall,
    llm,
    mock_llm_client,
    sent_message,
    no_transcript,
):
    """Bare `/ai` replying to a text message answers the replied-to message"""
    reply = _tg_message(10, "minji", text="What's the consensus on tongue cleaners?")
    mock_update.message.reply_to_message = reply

    await ai.handle(mock_update, mock_context)

    assert _prompt(mock_llm_client) == (
        "<replied_message>\n"
        "[#10 Thu Sep 24 18:05] @minji: What's the consensus on tongue cleaners?\n"
        "</replied_message>\n\n"
        "<request>\n[#789 Thu Sep 24 18:05] @arkits (replying to #10): (no text)\n</request>"
    )


@pytest.mark.asyncio
async def test_handle_reply_with_args(
    mock_update,
    mock_context,
    enabled_group,
    paywall,
    llm,
    mock_llm_client,
    sent_message,
    no_transcript,
):
    mock_context.args = ["is", "this", "true?"]
    mock_update.message.reply_to_message = _tg_message(
        10, "minji", text="Tongue cleaners are useless"
    )

    await ai.handle(mock_update, mock_context)

    prompt = _prompt(mock_llm_client)
    assert "[#10 Thu Sep 24 18:05] @minji: Tongue cleaners are useless" in prompt
    assert "[#789 Thu Sep 24 18:05] @arkits (replying to #10): is this true?" in prompt


@pytest.mark.asyncio
async def test_handle_reply_to_bot_is_labelled_as_self(
    mock_update,
    mock_context,
    enabled_group,
    paywall,
    llm,
    mock_llm_client,
    sent_message,
    no_transcript,
):
    mock_context.args = ["why?"]
    reply = _tg_message(10, "chaddi_bot", text="Because I said so")
    reply.from_user.id = mock_context.bot.id
    mock_update.message.reply_to_message = reply

    await ai.handle(mock_update, mock_context)

    assert f"[#10 Thu Sep 24 18:05] {ai.BOT_NAME}: Because I said so" in _prompt(mock_llm_client)


@pytest.mark.asyncio
async def test_handle_caption_strips_command_with_bot_username(
    mock_update,
    mock_context,
    enabled_group,
    paywall,
    llm,
    mock_llm_client,
    sent_message,
    no_transcript,
):
    """`/ai@botname question` in a caption only sends the question"""
    mock_update.message.caption = "/ai@chaddi_bot what is this?"

    await ai.handle(mock_update, mock_context)

    assert "@arkits: what is this?" in _prompt(mock_llm_client)


@pytest.mark.asyncio
async def test_handle_includes_transcript(
    mock_update, mock_context, enabled_group, paywall, llm, mock_llm_client, sent_message
):
    mock_context.args = ["thoughts?"]
    enabled_group.get_by_id.return_value.metadata["ai_thread_cleared_at"] = "2026-09-24T12:00:00"

    with patch(
        "src.bot.handlers.ai._build_transcript", return_value="[#1] @minji: chai?"
    ) as mock_transcript:
        await ai.handle(mock_update, mock_context)

    mock_transcript.assert_called_once_with(
        chat_id=456, exclude_message_ids={"789"}, since=datetime(2026, 9, 24, 12)
    )
    assert _prompt(mock_llm_client).startswith(
        "<chat_transcript>\n[#1] @minji: chai?\n</chat_transcript>\n\n<request>"
    )


# --- Files ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_handle_photo_in_request(
    mock_update,
    mock_context,
    enabled_group,
    paywall,
    llm,
    mock_llm_client,
    sent_message,
    no_transcript,
):
    photo = MagicMock(spec=PhotoSize)
    photo.file_size = 1000
    photo.get_file = _file_holder(b"jpeg bytes")
    mock_update.message.photo = [MagicMock(spec=PhotoSize), photo]
    mock_update.message.to_dict.return_value = {"photo": [{}]}

    await ai.handle(mock_update, mock_context)

    attachments = mock_llm_client.generate_streaming.call_args.kwargs["attachments"]
    assert attachments == [LLMAttachment(data=b"jpeg bytes", mime_type="image/jpeg")]
    prompt = _prompt(mock_llm_client)
    assert "- request: photo (attached as an image)" in prompt
    assert "@arkits: [photo]" in prompt


@pytest.mark.asyncio
async def test_handle_photo_in_request_and_reply(
    mock_update,
    mock_context,
    enabled_group,
    paywall,
    llm,
    mock_llm_client,
    sent_message,
    no_transcript,
):
    """Both the request's image and the replied-to image are sent"""
    for message, data in ((mock_update.message, b"mine"), (None, b"theirs")):
        photo = MagicMock(spec=PhotoSize)
        photo.file_size = 100
        photo.get_file = _file_holder(data)
        if message is None:
            message = _tg_message(10, "minji")
            mock_update.message.reply_to_message = message
        message.photo = [photo]

    await ai.handle(mock_update, mock_context)

    attachments = mock_llm_client.generate_streaming.call_args.kwargs["attachments"]
    assert [a.data for a in attachments] == [b"mine", b"theirs"]


@pytest.mark.asyncio
async def test_handle_text_file_is_inlined(
    mock_update,
    mock_context,
    enabled_group,
    paywall,
    llm,
    mock_llm_client,
    sent_message,
    no_transcript,
):
    mock_update.message.caption = "/ai review this file"
    mock_update.message.document = _document("main.py", "text/x-python", b"print('hi')\n")

    await ai.handle(mock_update, mock_context)

    prompt = _prompt(mock_llm_client)
    assert '- request: file "main.py" (contents in <file> below)' in prompt
    assert '<file name="main.py" from="request">\nprint(\'hi\')\n\n</file>' in prompt
    assert prompt.endswith("@arkits: review this file\n</request>")
    assert mock_llm_client.generate_streaming.call_args.kwargs["attachments"] == []


@pytest.mark.asyncio
async def test_handle_pdf_in_replied_message_is_attached(
    mock_update,
    mock_context,
    enabled_group,
    paywall,
    llm,
    mock_llm_client,
    sent_message,
    no_transcript,
):
    mock_context.args = ["summarise"]
    reply = _tg_message(10, "minji")
    reply.document = _document("report.pdf", "application/pdf", b"%PDF-1.7")
    mock_update.message.reply_to_message = reply

    await ai.handle(mock_update, mock_context)

    attachments = mock_llm_client.generate_streaming.call_args.kwargs["attachments"]
    assert attachments == [
        LLMAttachment(data=b"%PDF-1.7", mime_type="application/pdf", filename="report.pdf")
    ]
    assert '- replied message: file "report.pdf" (attached)' in _prompt(mock_llm_client)


@pytest.mark.asyncio
async def test_handle_skips_oversized_and_unsupported_files(
    mock_update,
    mock_context,
    enabled_group,
    paywall,
    llm,
    mock_llm_client,
    sent_message,
    no_transcript,
):
    mock_context.args = ["what", "are", "these?"]
    big = _document("huge.pdf", "application/pdf", size=ai.MAX_PDF_BYTES + 1)
    mock_update.message.document = big
    reply = _tg_message(10, "minji")
    reply.document = _document("clip.mp4", "video/mp4", size=100)
    mock_update.message.reply_to_message = reply

    await ai.handle(mock_update, mock_context)

    big.get_file.assert_not_called()
    reply.document.get_file.assert_not_called()
    prompt = _prompt(mock_llm_client)
    assert '- request: file "huge.pdf" (not included - too large (10.0 MB, limit 10.0 MB))' in (
        prompt
    )
    assert "unsupported file type (video/mp4)" in prompt
    assert mock_llm_client.generate_streaming.call_args.kwargs["attachments"] == []


@pytest.mark.asyncio
async def test_handle_binary_file_is_not_inlined(
    mock_update,
    mock_context,
    enabled_group,
    paywall,
    llm,
    mock_llm_client,
    sent_message,
    no_transcript,
):
    mock_update.message.caption = "/ai"
    mock_update.message.document = _document("x.zip", "application/zip", b"PK\x03\x04\x00\x00")

    await ai.handle(mock_update, mock_context)

    prompt = _prompt(mock_llm_client)
    assert "can't read this file type (application/zip)" in prompt
    assert "<file " not in prompt


@pytest.mark.asyncio
async def test_handle_long_text_file_is_truncated(
    mock_update,
    mock_context,
    enabled_group,
    paywall,
    llm,
    mock_llm_client,
    sent_message,
    no_transcript,
):
    mock_update.message.document = _document(
        "log.txt", "text/plain", b"a" * (ai.MAX_TEXT_FILE_CHARS + 10)
    )

    await ai.handle(mock_update, mock_context)

    assert "[truncated - showing the first 100,000 of 100,010 characters]" in _prompt(
        mock_llm_client
    )


@pytest.mark.asyncio
async def test_handle_failed_download_is_reported(
    mock_update,
    mock_context,
    enabled_group,
    paywall,
    llm,
    mock_llm_client,
    sent_message,
    no_transcript,
):
    document = _document("notes.md", "text/markdown", b"# hi")
    document.get_file = AsyncMock(side_effect=RuntimeError("network"))
    mock_update.message.document = document

    await ai.handle(mock_update, mock_context)

    assert "(not included - couldn't download it)" in _prompt(mock_llm_client)


# --- Responses --------------------------------------------------------------


@pytest.mark.asyncio
async def test_handle_markdown_parse_error(
    mock_update,
    mock_context,
    enabled_group,
    paywall,
    llm,
    mock_llm_client,
    sent_message,
    no_transcript,
):
    mock_context.args = ["test", "question"]
    mock_llm_client.generate_streaming.return_value = "**Response** with invalid markdown"
    sent_message.edit_text = AsyncMock(side_effect=[Exception("Markdown error"), None])

    await ai.handle(mock_update, mock_context)

    # Should edit twice - once with markdown, once without
    assert sent_message.edit_text.call_count == 2


@pytest.mark.asyncio
async def test_handle_long_response_is_split(
    mock_update,
    mock_context,
    enabled_group,
    paywall,
    llm,
    mock_llm_client,
    sent_message,
    no_transcript,
):
    mock_context.args = ["long", "please"]
    mock_llm_client.generate_streaming.return_value = ("word " * 1000 + "\n") * 2

    await ai.handle(mock_update, mock_context)

    edited = sent_message.edit_text.call_args[0][0]
    followups = [c[0][0] for c in sent_message.reply_text.call_args_list]
    assert len(edited) <= ai.MAX_MESSAGE_LENGTH
    assert followups
    assert all(len(f) <= ai.MAX_MESSAGE_LENGTH for f in followups)
    assert (edited + " " + " ".join(followups)).split() == ["word"] * 2000


@pytest.mark.asyncio
async def test_handle_saves_conversation_to_logged_usage(
    mock_update,
    mock_context,
    enabled_group,
    paywall,
    llm,
    mock_llm_client,
    sent_message,
    no_transcript,
):
    mock_context.args = ["hi"]
    mock_update.message.reply_to_message = _tg_message(10, "minji", text="yo")

    usage = MagicMock()
    usage.metadata = None
    with patch("src.bot.handlers.ai.dc.log_command_usage", return_value=usage):
        await ai.handle(mock_update, mock_context)

    assert usage.metadata == {
        "user_message": "@arkits (replying to #10): hi",
        "bot_response": "AI response text",
        "message_id": 789,
        "response_message_id": 790,
    }
    usage.save.assert_called_once()


@pytest.mark.asyncio
async def test_handle_passes_chat_history_tool(
    mock_update,
    mock_context,
    enabled_group,
    paywall,
    llm,
    mock_llm_client,
    sent_message,
    no_transcript,
):
    mock_context.args = ["what", "happened?"]

    await ai.handle(mock_update, mock_context)

    tools = mock_llm_client.generate_streaming.call_args.kwargs["tools"]
    assert len(tools) == 1
    assert llm.LLMTool.call_args.kwargs["name"] == "get_chat_history"


# --- Caption commands -------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "caption, routed",
    [
        ("/ai what is this", True),
        ("/AI", True),
        ("/ai@chaddi_bot what", True),
        ("/ai@other_bot what", False),
        ("/aim high", False),
        ("look /ai", False),
        (None, False),
    ],
)
async def test_handle_caption_command(mock_update, mock_context, caption, routed):
    mock_update.message.caption = caption

    with patch("src.bot.handlers.ai.handle", new=AsyncMock()) as mock_handle:
        await ai.handle_caption_command(mock_update, mock_context)

    assert mock_handle.called is routed


# --- System prompt ----------------------------------------------------------


def test_system_prompt_only_advertises_web_search_when_available():
    with_search = MagicMock(has_web_search=True, provider="openrouter")
    without_search = MagicMock(has_web_search=False, provider="openai")

    assert "web search" in ai._build_system_prompt(with_search, 1)
    assert "web search" not in ai._build_system_prompt(without_search, 1)


def test_system_prompt_only_mentions_tool_when_supported():
    assert "get_chat_history" in ai._build_system_prompt(MagicMock(provider="openrouter"), 42)
    assert "#42" in ai._build_system_prompt(MagicMock(provider="openrouter"), 42)
    gemini_prompt = ai._build_system_prompt(MagicMock(has_web_search=False, provider="gemini"), 42)
    assert "get_chat_history" not in gemini_prompt
    assert "# Tools" not in gemini_prompt


def test_system_prompt_names_the_group():
    client = MagicMock(provider="gemini")
    assert '"Bakchods"' in ai._build_system_prompt(client, 1, chat_title="Bakchods")
    assert "a Telegram group chat" in ai._build_system_prompt(client, 1)


# --- Transcript -------------------------------------------------------------


def _logged_message(message_id, text, username, reply_to=None, minute=0, extra=None):
    message = MagicMock()
    message.message_id = str(message_id)
    message.text = text
    message.time_sent = datetime(2026, 9, 24, 18, minute)
    message.from_bakchod.username = username
    update = {"message": {"message_id": message_id, **(extra or {})}}
    if reply_to is not None:
        update["message"]["reply_to_message"] = {"message_id": reply_to}
    message.update = update
    return message


def _usage(minute, **metadata):
    usage = MagicMock()
    usage.executed_at = datetime(2026, 9, 24, 18, minute)
    usage.metadata = metadata
    return usage


@patch("src.bot.handlers.ai._get_ai_exchanges")
@patch("src.bot.handlers.ai.message_dao")
def test_transcript_merges_messages_and_ai_exchanges(mock_message_dao, mock_exchanges):
    mock_message_dao.get_chat_messages.return_value = [
        _logged_message(10, "anyone up for chai?", "minji", minute=1),
        _logged_message(13, "lol", "minji", reply_to=12, minute=4),
        _logged_message(14, "@chaddi_bot hi", "minji", minute=5),
        _logged_message(20, "current request", "arkits", minute=9),
    ]
    mock_exchanges.return_value = [
        _usage(
            2,
            user_message="@arkits (replying to #10): should I?",
            bot_response="Obviously",
            message_id=11,
            response_message_id=12,
        ),
        # Legacy row, from before message ids were saved
        _usage(3, user_message="@arkits: old style", bot_response="old reply"),
        # A mention - the request is already in the message log
        _usage(5, user_message="@minji: hi", bot_response="hello", message_id=14),
        # The current request's own row, not answered yet
        _usage(9),
    ]

    transcript = ai._build_transcript(456, exclude_message_ids={"20"}, since=None)

    assert transcript == (
        "[#10 Thu Sep 24 18:01] @minji: anyone up for chai?\n"
        "[#11 Thu Sep 24 18:02] @arkits (replying to #10): should I?\n"
        f"[#12 Thu Sep 24 18:02] {ai.BOT_NAME} (replying to #11): Obviously\n"
        "[Thu Sep 24 18:03] @arkits: old style\n"
        f"[Thu Sep 24 18:03] {ai.BOT_NAME}: old reply\n"
        "[#13 Thu Sep 24 18:04] @minji (replying to #12): lol\n"
        "[#14 Thu Sep 24 18:05] @minji: @chaddi_bot hi\n"
        f"[Thu Sep 24 18:05] {ai.BOT_NAME} (replying to #14): hello"
    )
    mock_message_dao.get_chat_messages.assert_called_once_with(
        456, limit=ai.TRANSCRIPT_MESSAGE_LIMIT, since=None
    )
    # Fewer messages than the limit - the whole history is covered
    mock_exchanges.assert_called_once_with(456, since=None)


@patch("src.bot.handlers.ai._get_ai_exchanges", return_value=[])
@patch("src.bot.handlers.ai.message_dao")
def test_transcript_limits_exchanges_to_message_window(mock_message_dao, mock_exchanges):
    messages = [
        _logged_message(i, "x", "minji", minute=i % 60) for i in range(ai.TRANSCRIPT_MESSAGE_LIMIT)
    ]
    mock_message_dao.get_chat_messages.return_value = messages
    cleared = datetime(2026, 9, 1)

    ai._build_transcript(456, exclude_message_ids=set(), since=cleared)

    mock_exchanges.assert_called_once_with(456, since=messages[0].time_sent)


@patch("src.bot.handlers.ai._get_ai_exchanges", return_value=[])
@patch("src.bot.handlers.ai.message_dao")
def test_transcript_empty(mock_message_dao, mock_exchanges):
    mock_message_dao.get_chat_messages.return_value = []

    assert ai._build_transcript(456, exclude_message_ids=set(), since=None) is None


@patch("src.bot.handlers.ai.message_dao")
def test_transcript_errors_are_swallowed(mock_message_dao):
    mock_message_dao.get_chat_messages.side_effect = RuntimeError("db down")

    assert ai._build_transcript(456, exclude_message_ids=set(), since=None) is None


@patch("src.bot.handlers.ai._get_ai_exchanges")
@patch("src.bot.handlers.ai.message_dao")
def test_transcript_truncates_long_responses(mock_message_dao, mock_exchanges):
    mock_message_dao.get_chat_messages.return_value = []
    mock_exchanges.return_value = [_usage(1, bot_response="y" * 5000)]

    transcript = ai._build_transcript(456, exclude_message_ids=set(), since=None)

    assert transcript.endswith("y" * ai.TRANSCRIPT_MAX_RESPONSE_LENGTH + "…")


def test_get_thread_cleared_at():
    assert ai._get_thread_cleared_at(None) is None
    assert ai._get_thread_cleared_at(MagicMock(metadata={})) is None
    assert ai._get_thread_cleared_at(MagicMock(metadata={"ai_thread_cleared_at": "nope"})) is None
    assert ai._get_thread_cleared_at(
        MagicMock(metadata={"ai_thread_cleared_at": "2026-09-24T12:00:00"})
    ) == datetime(2026, 9, 24, 12)


@pytest.mark.parametrize(
    "stored, label",
    [
        ({"photo": [{}]}, "[photo]"),
        ({"document": {"file_name": "a.pdf"}}, "[file: a.pdf]"),
        ({"document": {}}, "[file]"),
        ({"animation": {}, "document": {"file_name": "x.mp4"}}, "[GIF]"),
        ({"sticker": {"emoji": "😂"}}, "[sticker 😂]"),
        ({"poll": {"question": "chai?"}}, "[poll: chai?]"),
        ({"voice": {}}, "[voice message]"),
        ({"text": "hi"}, None),
        ("garbage", None),
    ],
)
def test_media_label(stored, label):
    assert ai._media_label(stored) == label


# --- Chat history tool ------------------------------------------------------


@patch("src.bot.handlers.ai.message_dao")
def test_chat_history_tool_formats_messages(mock_message_dao):
    mock_message_dao.get_chat_messages.return_value = [
        _logged_message(10, "anyone up for chai?", "minji", minute=1),
        _logged_message(11, "always", "arkits", reply_to=10, minute=2),
        _logged_message(12, None, "minji", minute=3, extra={"photo": [{}], "caption": "this one"}),
    ]

    tool = ai._build_chat_history_tool(456)
    result = tool.handler(limit=5, search="chai")

    mock_message_dao.get_chat_messages.assert_called_once_with(
        456, limit=5, before_message_id=None, search="chai"
    )
    assert result == (
        "[#10 Thu Sep 24 18:01] @minji: anyone up for chai?\n"
        "[#11 Thu Sep 24 18:02] @arkits (replying to #10): always\n"
        "[#12 Thu Sep 24 18:03] @minji: [photo] this one"
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
