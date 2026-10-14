from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.bot.handlers import ai_format, ai_history
from src.bot.handlers.ai_format import BOT_NAME


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


# --- Transcript -------------------------------------------------------------


@patch("src.bot.handlers.ai_history.get_ai_exchanges")
@patch("src.bot.handlers.ai_history.message_dao")
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
            response_message_ids=[12],
        ),
        # Legacy row, from before message ids were saved
        _usage(3, user_message="@arkits: old style", bot_response="old reply"),
        # A mention - the request is already in the message log
        _usage(5, user_message="@minji: hi", bot_response="hello", message_id=14),
        # The current request's own row, not answered yet
        _usage(9),
    ]

    transcript = ai_history.build_transcript(456, exclude_message_ids={"20"}, since=None)

    assert transcript.text == (
        "[#10 Thu Sep 24 18:01] @minji: anyone up for chai?\n"
        "[#11 Thu Sep 24 18:02] @arkits (replying to #10): should I?\n"
        f"[#12 Thu Sep 24 18:02] {BOT_NAME} (replying to #11): Obviously\n"
        "[Thu Sep 24 18:03] @arkits: old style\n"
        f"[Thu Sep 24 18:03] {BOT_NAME}: old reply\n"
        "[#13 Thu Sep 24 18:04] @minji (replying to #12): lol\n"
        "[#14 Thu Sep 24 18:05] @minji: @chaddi_bot hi\n"
        f"[Thu Sep 24 18:05] {BOT_NAME} (replying to #14): hello"
    )
    assert transcript.oldest_message_id == "10"
    assert transcript.truncated is False
    mock_message_dao.get_chat_messages.assert_called_once_with(
        456, limit=ai_history.TRANSCRIPT_MESSAGE_LIMIT, since=None
    )
    # Fewer messages than the limit - the whole history is covered
    mock_exchanges.assert_called_once_with(456, since=None)


@patch("src.bot.handlers.ai_history.get_ai_exchanges", return_value=[])
@patch("src.bot.handlers.ai_history.message_dao")
def test_transcript_limits_exchanges_to_message_window(mock_message_dao, mock_exchanges):
    messages = [
        _logged_message(i, "x", "minji", minute=i % 60)
        for i in range(ai_history.TRANSCRIPT_MESSAGE_LIMIT)
    ]
    mock_message_dao.get_chat_messages.return_value = messages

    transcript = ai_history.build_transcript(
        456, exclude_message_ids=set(), since=datetime(2026, 9, 1)
    )

    assert transcript.truncated is True
    mock_exchanges.assert_called_once_with(456, since=messages[0].time_sent)


@patch("src.bot.handlers.ai_history.get_ai_exchanges", return_value=[])
@patch("src.bot.handlers.ai_history.message_dao")
def test_transcript_empty(mock_message_dao, mock_exchanges):
    mock_message_dao.get_chat_messages.return_value = []

    transcript = ai_history.build_transcript(456, exclude_message_ids=set(), since=None)

    assert transcript.text is None
    assert transcript.oldest_message_id is None


@patch("src.bot.handlers.ai_history.message_dao")
def test_transcript_errors_are_swallowed(mock_message_dao):
    mock_message_dao.get_chat_messages.side_effect = RuntimeError("db down")

    assert ai_history.build_transcript(456, exclude_message_ids=set(), since=None).text is None


@patch("src.bot.handlers.ai_history.get_ai_exchanges")
@patch("src.bot.handlers.ai_history.message_dao")
def test_transcript_truncates_long_responses(mock_message_dao, mock_exchanges):
    mock_message_dao.get_chat_messages.return_value = []
    mock_exchanges.return_value = [_usage(1, bot_response="y" * 5000)]

    transcript = ai_history.build_transcript(456, exclude_message_ids=set(), since=None)

    assert transcript.text.endswith("y" * ai_history.TRANSCRIPT_MAX_RESPONSE_LENGTH + "…")


def test_get_thread_cleared_at():
    assert ai_history.get_thread_cleared_at(None) is None
    assert ai_history.get_thread_cleared_at(MagicMock(metadata={})) is None
    assert (
        ai_history.get_thread_cleared_at(MagicMock(metadata={"ai_thread_cleared_at": "nope"}))
        is None
    )
    assert ai_history.get_thread_cleared_at(
        MagicMock(metadata={"ai_thread_cleared_at": "2026-09-24T12:00:00"})
    ) == datetime(2026, 9, 24, 12)


# --- Finding /ai responses --------------------------------------------------


def test_response_message_ids():
    assert ai_history.response_message_ids(_usage(1, response_message_ids=[5, 6])) == ["5", "6"]
    assert ai_history.response_message_ids(_usage(1, response_message_id=5)) == ["5"]
    assert ai_history.response_message_ids(_usage(1)) == []


@patch("src.bot.handlers.ai_history.CommandUsage")
def test_find_ai_exchange(mock_command_usage):
    match = _usage(2, response_message_ids=[50, 51])
    query = mock_command_usage.select.return_value
    query.where.return_value = query
    query.order_by.return_value.limit.return_value = [_usage(3, response_message_id=60), match]

    assert ai_history.find_ai_exchange(456, 51) is match
    assert ai_history.find_ai_exchange(456, 99) is None
    assert ai_history.is_ai_response(456, "50") is True


@patch("src.bot.handlers.ai_history.find_ai_exchange", side_effect=RuntimeError("db down"))
def test_is_ai_response_errors_are_false(mock_find):
    assert ai_history.is_ai_response(456, 1) is False


# --- Summary ----------------------------------------------------------------


def test_get_summary():
    group = MagicMock(metadata={"ai_summary": {"text": "stuff", "until": "2026-09-24T15:00:00"}})

    summary = ai_history.get_summary(group, since=None)
    assert summary == {"text": "stuff", "until": datetime(2026, 9, 24, 15)}
    # A thread clear after the summary hides it
    assert ai_history.get_summary(group, since=datetime(2026, 9, 24, 16)) is None
    assert ai_history.get_summary(MagicMock(metadata={}), since=None) is None
    assert ai_history.format_summary(summary) == (
        '<earlier_summary until="Thu Sep 24 15:00">\nstuff\n</earlier_summary>'
    )
    assert ai_history.format_summary(None) is None


@pytest.mark.asyncio
@patch("src.bot.handlers.ai_history.Group")
@patch("src.bot.handlers.ai_history.message_dao")
async def test_update_summary(mock_message_dao, mock_group_class):
    messages = [
        _logged_message(i, f"msg {i}", "minji", minute=i % 60)
        for i in range(ai_history.SUMMARY_MIN_NEW_MESSAGES)
    ]
    mock_message_dao.get_chat_messages.return_value = messages
    group = MagicMock(metadata={"enabled_commands": ["ai"]})
    mock_group_class.get_by_id.return_value = group
    client = MagicMock()
    client.complete = AsyncMock(return_value=" new summary ")
    previous = {"text": "old summary", "until": datetime(2026, 9, 24, 12)}
    transcript = ai_history.Transcript("lines", oldest_message_id="500", truncated=True)

    await ai_history.update_summary(client, 456, transcript, since=None, previous=previous)

    mock_message_dao.get_chat_messages.assert_called_once_with(
        456,
        limit=ai_history.SUMMARY_MAX_BATCH,
        before_message_id="500",
        since=datetime(2026, 9, 24, 12),
    )
    prompt = client.complete.call_args.args[0][0]["content"]
    assert prompt.startswith("<summary_so_far>\nold summary\n</summary_so_far>")
    assert "@minji: msg 0" in prompt
    saved = group.metadata["ai_summary"]
    assert saved["text"] == "new summary"
    assert saved["until"] == messages[-1].time_sent.isoformat()
    assert group.metadata["enabled_commands"] == ["ai"]
    group.save.assert_called_once()
    assert "456" not in ai_history._summaries_in_progress


@pytest.mark.asyncio
@patch("src.bot.handlers.ai_history.message_dao")
async def test_update_summary_waits_for_enough_messages(mock_message_dao):
    mock_message_dao.get_chat_messages.return_value = [_logged_message(1, "x", "minji")]
    client = MagicMock()
    client.complete = AsyncMock()
    transcript = ai_history.Transcript("lines", oldest_message_id="500", truncated=True)

    await ai_history.update_summary(client, 456, transcript, since=None, previous=None)

    assert not client.complete.called


@pytest.mark.asyncio
async def test_update_summary_skips_uncut_transcript():
    client = MagicMock()
    client.complete = AsyncMock()

    await ai_history.update_summary(
        client, 456, ai_history.Transcript("lines"), since=None, previous=None
    )

    assert not client.complete.called


@pytest.mark.asyncio
@patch("src.bot.handlers.ai_history.message_dao")
async def test_update_summary_respects_thread_clear(mock_message_dao):
    """A clear after the previous summary means only messages since the clear count"""
    mock_message_dao.get_chat_messages.return_value = []
    cleared = datetime(2026, 9, 24, 16)
    previous = {"text": "old", "until": datetime(2026, 9, 24, 12)}
    transcript = ai_history.Transcript("lines", oldest_message_id="500", truncated=True)

    await ai_history.update_summary(MagicMock(), 456, transcript, since=cleared, previous=previous)

    assert mock_message_dao.get_chat_messages.call_args.kwargs["since"] == cleared


# --- Memory -----------------------------------------------------------------


@pytest.fixture
def memory_group():
    group = MagicMock(metadata={"enabled_commands": ["ai"]})
    with patch("src.bot.handlers.ai_history.Group") as mock_group_class:
        mock_group_class.get_by_id.return_value = group
        yield group


def test_add_and_remove_memory(memory_group):
    first = ai_history.add_memory(456, " likes chai ", "@minji", added_by="@arkits")
    second = ai_history.add_memory(456, "trip is on Dec 5", None, added_by="@arkits")

    assert first["id"] == 1
    assert second["id"] == 2
    memories = ai_history.get_memories(memory_group)
    assert [m["text"] for m in memories] == ["likes chai", "trip is on Dec 5"]
    assert ai_history.format_memories(memories) == (
        "- [1] (about @minji) likes chai\n- [2] trip is on Dec 5"
    )

    assert ai_history.remove_memory(456, 1)["text"] == "likes chai"
    assert ai_history.remove_memory(456, 1) is None
    assert [m["id"] for m in ai_history.get_memories(memory_group)] == [2]
    # New ids don't reuse old ones while later notes exist
    assert ai_history.add_memory(456, "x", None, added_by="@arkits")["id"] == 3


@pytest.mark.parametrize(
    "note, error",
    [("", "empty"), ("x" * (ai_history.MAX_MEMORY_LENGTH + 1), "at most")],
)
def test_add_memory_rejects_bad_notes(memory_group, note, error):
    with pytest.raises(ValueError, match=error):
        ai_history.add_memory(456, note, None, added_by="@arkits")


def test_add_memory_when_full(memory_group):
    memory_group.metadata["ai_memory"] = [
        {"id": i, "text": "x"} for i in range(ai_history.MAX_MEMORIES)
    ]

    with pytest.raises(ValueError, match="full"):
        ai_history.add_memory(456, "one more", None, added_by="@arkits")


def test_format_memories_empty():
    assert ai_history.format_memories([]) is None
    assert ai_history.get_memories(MagicMock(metadata={"ai_memory": "junk"})) == []


# --- Formatting -------------------------------------------------------------


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
    assert ai_format.media_label(stored) == label


def test_format_chat_message_with_media_quote_and_reply():
    message = _logged_message(
        12,
        None,
        "minji",
        reply_to=10,
        minute=3,
        extra={"photo": [{}], "caption": "this one", "quote": {"text": "q" * 300}},
    )

    assert ai_format.format_chat_message(message) == (
        f'[#12 Thu Sep 24 18:03] @minji (replying to #10, quoting "{"q" * 200}…"): [photo] this one'
    )


def test_format_time_and_local_naive():
    from datetime import UTC

    aware = datetime(2026, 9, 24, 12, tzinfo=UTC)
    assert ai_format.to_local_naive(aware).tzinfo is None
    assert ai_format.to_local_naive("nope") is None
    assert ai_format.format_time(None) is None
    assert ai_format.format_header(None, None) == ""
