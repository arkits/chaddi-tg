from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Chat, Document, Message, PhotoSize, Update, User
from telegram.ext import ContextTypes

from src.bot.handlers import ai
from src.bot.handlers.ai_files import MAX_PDF_BYTES, MAX_TEXT_FILE_CHARS
from src.bot.handlers.ai_format import BOT_NAME
from src.bot.handlers.ai_history import Transcript
from src.domain.ai import LLMAttachment, LLMTool

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
    message.media_group_id = None
    message.quote = None
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
    context.application = MagicMock()
    # Close scheduled coroutines so tests don't warn about them never being awaited
    context.application.create_task.side_effect = lambda coro, **kwargs: coro.close()
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
    """Patch the ai module the handler uses."""
    with patch("src.bot.handlers.ai.ai") as mock_ai_module:
        mock_ai_module.get_default_client.return_value = mock_llm_client
        yield mock_ai_module


@pytest.fixture
def message_log():
    with patch("src.bot.handlers.ai.message_dao") as mock_message_dao:
        mock_message_dao.get_messages_between.return_value = []
        yield mock_message_dao


@pytest.fixture
def no_transcript():
    with patch(
        "src.bot.handlers.ai.build_transcript", return_value=Transcript(text=None)
    ) as mock_transcript:
        yield mock_transcript


@pytest.fixture
def ready(enabled_group, paywall, llm, sent_message, message_log, no_transcript):
    """Everything a request needs to reach the model."""
    return None


def _prompt(mock_llm_client) -> str:
    messages = mock_llm_client.generate_streaming.call_args.kwargs["messages"]
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    return messages[0]["content"]


def _kwargs(mock_llm_client) -> dict:
    return mock_llm_client.generate_streaming.call_args.kwargs


def _file_holder(data: bytes):
    """A get_file() that downloads `data`."""
    telegram_file = AsyncMock()
    telegram_file.download_as_bytearray = AsyncMock(return_value=bytearray(data))
    return AsyncMock(return_value=telegram_file)


def _photo(data: bytes, size=100):
    photo = MagicMock(spec=PhotoSize)
    photo.file_size = size
    photo.get_file = _file_holder(data)
    return photo


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
async def test_handle_command_logging(mock_update, mock_context, ready):
    mock_context.args = ["test", "question"]

    with patch("src.bot.handlers.ai.dc.log_command_usage") as mock_log:
        await ai.handle(mock_update, mock_context)

    mock_log.assert_called_once_with("ai", mock_update)


@pytest.mark.asyncio
async def test_handle_logs_command_message(mock_update, mock_context, ready, message_log):
    """/ai commands skip the message logger, so the handler logs them itself"""
    mock_context.args = ["hi"]
    message_log.get_message.return_value = None

    await ai.handle(mock_update, mock_context)

    message_log.get_message.assert_called_once_with(456, 789)
    message_log.log_message_from_update.assert_called_once_with(mock_update)


@pytest.mark.asyncio
async def test_handle_doesnt_relog_mentions(mock_update, mock_context, ready, message_log):
    message_log.get_message.return_value = MagicMock()

    await ai.handle(mock_update, mock_context, question="hi", quiet=True)

    assert not message_log.log_message_from_update.called


def test_handle_in_background(mock_update, mock_context):
    ai.handle_in_background(mock_update, mock_context, question="hi", quiet=True)

    mock_context.application.create_task.assert_called_once()
    assert mock_context.application.create_task.call_args.kwargs["update"] is mock_update


# --- Prompt -----------------------------------------------------------------


@pytest.mark.asyncio
async def test_handle_with_args(mock_update, mock_context, ready, mock_llm_client):
    mock_context.args = ["what", "is", "AI?"]

    await ai.handle(mock_update, mock_context)

    assert _prompt(mock_llm_client) == (
        "<request>\n[#789 Thu Sep 24 18:05] @arkits: what is AI?\n</request>"
    )
    kwargs = _kwargs(mock_llm_client)
    assert kwargs["attachments"] == []
    assert '"Bakchods"' in kwargs["system_prompt"]


@pytest.mark.asyncio
async def test_handle_question_param(mock_update, mock_context, ready, mock_llm_client):
    """The question param is used when there are no command args (the mention path)"""
    await ai.handle(mock_update, mock_context, question="how much is 10000 divided by 12")

    assert "@arkits: how much is 10000 divided by 12" in _prompt(mock_llm_client)


@pytest.mark.asyncio
async def test_handle_reply_without_args(mock_update, mock_context, ready, mock_llm_client):
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
async def test_handle_reply_with_args(mock_update, mock_context, ready, mock_llm_client):
    mock_context.args = ["is", "this", "true?"]
    mock_update.message.reply_to_message = _tg_message(
        10, "minji", text="Tongue cleaners are useless"
    )

    await ai.handle(mock_update, mock_context)

    prompt = _prompt(mock_llm_client)
    assert "[#10 Thu Sep 24 18:05] @minji: Tongue cleaners are useless" in prompt
    assert "[#789 Thu Sep 24 18:05] @arkits (replying to #10): is this true?" in prompt


@pytest.mark.asyncio
async def test_handle_partial_quote(mock_update, mock_context, ready, mock_llm_client):
    """Replying with a quote of part of the message tells the model which part"""
    mock_context.args = ["source?"]
    mock_update.message.reply_to_message = _tg_message(10, "minji", text="a. b is true. c.")
    mock_update.message.quote = MagicMock(text="b is true")

    await ai.handle(mock_update, mock_context)

    assert '@arkits (replying to #10, quoting "b is true"): source?' in _prompt(mock_llm_client)


@pytest.mark.asyncio
async def test_handle_reply_to_bot_is_labelled_as_self(
    mock_update, mock_context, ready, mock_llm_client
):
    mock_context.args = ["why?"]
    reply = _tg_message(10, "chaddi_bot", text="Because I said so")
    reply.from_user.id = mock_context.bot.id
    mock_update.message.reply_to_message = reply

    await ai.handle(mock_update, mock_context)

    assert f"[#10 Thu Sep 24 18:05] {BOT_NAME}: Because I said so" in _prompt(mock_llm_client)


@pytest.mark.asyncio
async def test_handle_caption_strips_command_with_bot_username(
    mock_update, mock_context, ready, mock_llm_client
):
    """`/ai@botname question` in a caption only sends the question"""
    mock_update.message.caption = "/ai@chaddi_bot what is this?"

    await ai.handle(mock_update, mock_context)

    assert "@arkits: what is this?" in _prompt(mock_llm_client)


@pytest.mark.asyncio
async def test_handle_includes_transcript_and_summary(
    mock_update,
    mock_context,
    enabled_group,
    paywall,
    llm,
    mock_llm_client,
    sent_message,
    message_log,
):
    mock_context.args = ["thoughts?"]
    enabled_group.get_by_id.return_value.metadata.update(
        ai_thread_cleared_at="2026-09-24T12:00:00",
        ai_summary={"text": "they planned a trip", "until": "2026-09-24T15:00:00"},
    )

    with patch(
        "src.bot.handlers.ai.build_transcript", return_value=Transcript("[#1] @minji: chai?")
    ) as mock_transcript:
        await ai.handle(mock_update, mock_context)

    mock_transcript.assert_called_once_with(
        chat_id=456, exclude_message_ids={"789"}, since=datetime(2026, 9, 24, 12)
    )
    assert _prompt(mock_llm_client).startswith(
        '<earlier_summary until="Thu Sep 24 15:00">\nthey planned a trip\n</earlier_summary>\n\n'
        "<chat_transcript>\n[#1] @minji: chai?\n</chat_transcript>\n\n<request>"
    )
    # Not cut off, so there's nothing new to summarise
    assert not mock_context.application.create_task.called


@pytest.mark.asyncio
async def test_handle_updates_summary_when_transcript_is_cut_off(
    mock_update, mock_context, enabled_group, paywall, llm, sent_message, message_log
):
    mock_context.args = ["hi"]
    transcript = Transcript("lines", oldest_message_id="5", truncated=True)

    with (
        patch("src.bot.handlers.ai.build_transcript", return_value=transcript),
        patch("src.bot.handlers.ai.update_summary", new=MagicMock()) as mock_update_summary,
    ):
        mock_context.application.create_task.side_effect = None
        await ai.handle(mock_update, mock_context)

    assert mock_update_summary.call_args.args[1:] == (456, transcript, None, None)
    mock_context.application.create_task.assert_called_once_with(mock_update_summary.return_value)


@pytest.mark.asyncio
async def test_handle_includes_memories(
    mock_update, mock_context, ready, enabled_group, mock_llm_client
):
    mock_context.args = ["hi"]
    enabled_group.get_by_id.return_value.metadata["ai_memory"] = [
        {"id": 1, "text": "hates pineapple pizza", "about": "@minji"}
    ]

    await ai.handle(mock_update, mock_context)

    system_prompt = _kwargs(mock_llm_client)["system_prompt"]
    assert "# What you remember about this group" in system_prompt
    assert "- [1] (about @minji) hates pineapple pizza" in system_prompt


@pytest.mark.asyncio
async def test_handle_passes_tools(mock_update, mock_context, ready, mock_llm_client):
    mock_context.args = ["what", "happened?"]

    await ai.handle(mock_update, mock_context)

    tools = _kwargs(mock_llm_client)["tools"]
    assert {t.name for t in tools} == {
        "get_chat_history",
        "read_message",
        "fetch_url",
        "set_reminder",
        "generate_image",
        "create_poll",
        "remember",
        "forget",
    }


@pytest.mark.asyncio
async def test_handle_shows_tool_progress(
    mock_update, mock_context, ready, mock_llm_client, sent_message
):
    mock_context.args = ["what's on example.com?"]
    tool = LLMTool("fetch_url", "", {}, handler=lambda url: "", status=lambda a: f"🌐 {a['url']}")

    async def generate(**kwargs):
        await kwargs["on_tool_call"](tool, {"url": "example.com"})
        return "done"

    mock_llm_client.generate_streaming.side_effect = generate

    await ai.handle(mock_update, mock_context)

    sent_message.edit_text.assert_any_call("🌐 example.com")


# --- Files ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_handle_photo_in_request(mock_update, mock_context, ready, mock_llm_client):
    mock_update.message.photo = [MagicMock(spec=PhotoSize), _photo(b"jpeg bytes", size=1000)]
    mock_update.message.to_dict.return_value = {"photo": [{}]}

    await ai.handle(mock_update, mock_context)

    assert _kwargs(mock_llm_client)["attachments"] == [
        LLMAttachment(data=b"jpeg bytes", mime_type="image/jpeg")
    ]
    prompt = _prompt(mock_llm_client)
    assert "- request: photo (attached as an image)" in prompt
    assert "@arkits: [photo]" in prompt


@pytest.mark.asyncio
async def test_handle_photo_in_request_and_reply(mock_update, mock_context, ready, mock_llm_client):
    """Both the request's image and the replied-to image are sent"""
    mock_update.message.photo = [_photo(b"mine")]
    reply = _tg_message(10, "minji")
    reply.photo = [_photo(b"theirs")]
    mock_update.message.reply_to_message = reply

    await ai.handle(mock_update, mock_context)

    assert [a.data for a in _kwargs(mock_llm_client)["attachments"]] == [b"mine", b"theirs"]


@pytest.mark.asyncio
async def test_handle_album_in_request(
    mock_update, mock_context, ready, mock_llm_client, message_log
):
    """The rest of an album sent with an /ai caption is attached too"""
    mock_update.message.caption = "/ai which is best?"
    mock_update.message.photo = [_photo(b"first")]
    mock_update.message.media_group_id = "album-1"

    def logged(message_id, album_id):
        row = MagicMock()
        row.message_id = str(message_id)
        row.update = {
            "message": {
                "message_id": message_id,
                "media_group_id": album_id,
                "photo": [{"file_id": f"small-{message_id}"}, {"file_id": f"big-{message_id}"}],
            }
        }
        return row

    message_log.get_messages_between.return_value = [
        logged(789, "album-1"),  # the request itself
        logged(790, "album-1"),
        logged(791, "other-album"),
        logged(792, "album-1"),
    ]
    downloads = {"big-790": b"second", "big-792": b"third"}

    async def get_file(file_id):
        telegram_file = AsyncMock()
        telegram_file.download_as_bytearray = AsyncMock(return_value=bytearray(downloads[file_id]))
        return telegram_file

    mock_context.bot.get_file = get_file

    with patch("src.bot.handlers.ai.asyncio.sleep", new=AsyncMock()) as mock_sleep:
        await ai.handle(mock_update, mock_context)

    mock_sleep.assert_awaited_once_with(ai.ALBUM_WAIT_SECONDS)
    assert [a.data for a in _kwargs(mock_llm_client)["attachments"]] == [
        b"first",
        b"second",
        b"third",
    ]
    assert "- request's album: photo (attached as an image)" in _prompt(mock_llm_client)


@pytest.mark.asyncio
async def test_handle_text_file_is_inlined(mock_update, mock_context, ready, mock_llm_client):
    mock_update.message.caption = "/ai review this file"
    mock_update.message.document = _document("main.py", "text/x-python", b"print('hi')\n")

    await ai.handle(mock_update, mock_context)

    prompt = _prompt(mock_llm_client)
    assert '- request: file "main.py" (contents in <file> below)' in prompt
    assert '<file name="main.py" from="request">\nprint(\'hi\')\n\n</file>' in prompt
    assert prompt.endswith("@arkits: review this file\n</request>")
    assert _kwargs(mock_llm_client)["attachments"] == []


@pytest.mark.asyncio
async def test_handle_pdf_in_replied_message_is_attached(
    mock_update, mock_context, ready, mock_llm_client
):
    mock_context.args = ["summarise"]
    reply = _tg_message(10, "minji")
    reply.document = _document("report.pdf", "application/pdf", b"%PDF-1.7")
    mock_update.message.reply_to_message = reply

    await ai.handle(mock_update, mock_context)

    assert _kwargs(mock_llm_client)["attachments"] == [
        LLMAttachment(data=b"%PDF-1.7", mime_type="application/pdf", filename="report.pdf")
    ]
    assert '- replied message: file "report.pdf" (attached)' in _prompt(mock_llm_client)


@pytest.mark.asyncio
async def test_handle_skips_oversized_and_unsupported_files(
    mock_update, mock_context, ready, mock_llm_client
):
    mock_context.args = ["what", "are", "these?"]
    big = _document("huge.pdf", "application/pdf", size=MAX_PDF_BYTES + 1)
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
    assert _kwargs(mock_llm_client)["attachments"] == []


@pytest.mark.asyncio
async def test_handle_binary_file_is_not_inlined(mock_update, mock_context, ready, mock_llm_client):
    mock_update.message.caption = "/ai"
    mock_update.message.document = _document("x.zip", "application/zip", b"PK\x03\x04\x00\x00")

    await ai.handle(mock_update, mock_context)

    prompt = _prompt(mock_llm_client)
    assert "can't read this file type (application/zip)" in prompt
    assert "<file " not in prompt


@pytest.mark.asyncio
async def test_handle_long_text_file_is_truncated(
    mock_update, mock_context, ready, mock_llm_client
):
    mock_update.message.document = _document(
        "log.txt", "text/plain", b"a" * (MAX_TEXT_FILE_CHARS + 10)
    )

    await ai.handle(mock_update, mock_context)

    assert "[truncated - showing the first 100,000 of 100,010 characters]" in _prompt(
        mock_llm_client
    )


@pytest.mark.asyncio
async def test_handle_failed_download_is_reported(
    mock_update, mock_context, ready, mock_llm_client
):
    document = _document("notes.md", "text/markdown", b"# hi")
    document.get_file = AsyncMock(side_effect=RuntimeError("network"))
    mock_update.message.document = document

    await ai.handle(mock_update, mock_context)

    assert "(not included - couldn't download it)" in _prompt(mock_llm_client)


# --- Responses --------------------------------------------------------------


@pytest.mark.asyncio
async def test_handle_markdown_parse_error(
    mock_update, mock_context, ready, mock_llm_client, sent_message
):
    mock_context.args = ["test", "question"]
    mock_llm_client.generate_streaming.return_value = "**Response** with invalid markdown"
    sent_message.edit_text = AsyncMock(side_effect=[Exception("Markdown error"), None])

    await ai.handle(mock_update, mock_context)

    # Should edit twice - once with markdown, once without
    assert sent_message.edit_text.call_count == 2


@pytest.mark.asyncio
async def test_handle_long_response_is_split(
    mock_update, mock_context, ready, mock_llm_client, sent_message
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
    mock_update, mock_context, ready, mock_llm_client, sent_message
):
    mock_context.args = ["hi"]
    mock_update.message.reply_to_message = _tg_message(10, "minji", text="yo")
    mock_llm_client.generate_streaming.return_value = "a\n" + "b" * ai.MAX_MESSAGE_LENGTH
    sent_message.reply_text = AsyncMock(return_value=MagicMock(message_id=791))

    usage = MagicMock()
    usage.metadata = None
    with patch("src.bot.handlers.ai.dc.log_command_usage", return_value=usage):
        await ai.handle(mock_update, mock_context)

    assert usage.metadata == {
        "user_message": "@arkits (replying to #10): hi",
        "bot_response": "a\n" + "b" * ai.MAX_MESSAGE_LENGTH,
        "message_id": 789,
        "response_message_id": 790,
        "response_message_ids": [790, 791],
    }
    usage.save.assert_called_once()


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

    assert "Real-time web search" in ai._build_system_prompt(with_search, 1)
    assert "Real-time web search" not in ai._build_system_prompt(without_search, 1)


def test_system_prompt_lists_tools_and_request_id():
    prompt = ai._build_system_prompt(MagicMock(provider="openrouter"), 42)
    assert "#42" in prompt
    for tool in ("get_chat_history", "read_message", "fetch_url", "set_reminder", "remember"):
        assert tool in prompt
    assert "What you remember" not in prompt


def test_system_prompt_names_the_group():
    client = MagicMock(provider="openrouter")
    assert '"Bakchods"' in ai._build_system_prompt(client, 1, chat_title="Bakchods")
    assert "a Telegram group chat" in ai._build_system_prompt(client, 1)


def test_split_message():
    assert ai._split_message("short") == ["short"]
    assert ai._split_message("") == [""]
    assert ai._split_message("aaaa\nbbbb", limit=6) == ["aaaa", "bbbb"]
    assert ai._split_message("aaa bbb ccc", limit=8) == ["aaa bbb", "ccc"]
    assert ai._split_message("abcdefgh", limit=3) == ["abc", "def", "gh"]
