import socket
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.bot.handlers import ai_tools
from src.domain.ai import LLMAttachment


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


@pytest.fixture
def ctx():
    bot = MagicMock()
    bot.send_photo = AsyncMock(return_value=MagicMock(message_id=900))
    bot.send_poll = AsyncMock(return_value=MagicMock(message_id=901))
    return ai_tools.ToolContext(
        bot=bot,
        job_queue=MagicMock(),
        chat_id=456,
        request_message_id=789,
        user_id=123,
        user_name="@arkits",
    )


def _tool(ctx, name):
    return next(t for t in ai_tools.build_tools(ctx) if t.name == name)


async def _call(tool, **kwargs):
    result = tool.handler(**kwargs)
    if hasattr(result, "__await__"):
        result = await result
    return result


# --- Chat history -----------------------------------------------------------


@patch("src.bot.handlers.ai_tools.message_dao")
def test_chat_history_tool_formats_messages(mock_message_dao):
    mock_message_dao.get_chat_messages.return_value = [
        _logged_message(10, "anyone up for chai?", "minji", minute=1),
        _logged_message(11, "always", "arkits", reply_to=10, minute=2),
        _logged_message(12, None, "minji", minute=3, extra={"photo": [{}], "caption": "this one"}),
    ]

    tool = ai_tools.chat_history_tool(456)
    result = tool.handler(limit=5, search="chai")

    mock_message_dao.get_chat_messages.assert_called_once_with(
        456, limit=5, before_message_id=None, search="chai"
    )
    assert result == (
        "[#10 Thu Sep 24 18:01] @minji: anyone up for chai?\n"
        "[#11 Thu Sep 24 18:02] @arkits (replying to #10): always\n"
        "[#12 Thu Sep 24 18:03] @minji: [photo] this one"
    )
    assert tool.describe({"search": "chai"}) == '🔎 searching the chat for "chai"…'
    assert tool.describe({}) == "📜 scrolling up the chat…"


@patch("src.bot.handlers.ai_tools.message_dao")
def test_chat_history_tool_clamps_limit_and_truncates(mock_message_dao):
    mock_message_dao.get_chat_messages.return_value = [_logged_message(10, "x" * 1000, "minji")]

    result = ai_tools.chat_history_tool(456).handler(limit=10_000, before_message_id=99)

    kwargs = mock_message_dao.get_chat_messages.call_args.kwargs
    assert kwargs["limit"] == ai_tools.CHAT_HISTORY_MAX_LIMIT
    assert kwargs["before_message_id"] == 99
    assert result.endswith("x" * 500 + "…")


@patch("src.bot.handlers.ai_tools.message_dao")
def test_chat_history_tool_no_messages(mock_message_dao):
    mock_message_dao.get_chat_messages.return_value = []

    assert ai_tools.chat_history_tool(456).handler() == "No messages found."


# --- read_message -----------------------------------------------------------


@pytest.mark.asyncio
@patch("src.bot.handlers.ai_tools.message_dao")
async def test_read_message_with_photo(mock_message_dao, ctx):
    mock_message_dao.get_message.return_value = _logged_message(
        10,
        None,
        "minji",
        extra={"caption": "look", "photo": [{"file_id": "small"}, {"file_id": "big"}]},
    )
    telegram_file = AsyncMock()
    telegram_file.download_as_bytearray = AsyncMock(return_value=bytearray(b"jpeg"))
    ctx.bot.get_file = AsyncMock(return_value=telegram_file)

    result = await _call(_tool(ctx, "read_message"), message_id=10)

    ctx.bot.get_file.assert_awaited_once_with("big")
    mock_message_dao.get_message.assert_called_once_with(456, 10)
    assert result.attachments == [LLMAttachment(b"jpeg", "image/jpeg")]
    assert result.text == (
        "[#10 Thu Sep 24 18:00] @minji: [photo] look\n- message #10: photo (attached as an image)"
    )


@pytest.mark.asyncio
@patch("src.bot.handlers.ai_tools.message_dao")
async def test_read_message_with_text_file(mock_message_dao, ctx):
    mock_message_dao.get_message.return_value = _logged_message(
        10,
        None,
        "minji",
        extra={"document": {"file_id": "f", "file_name": "a.py", "mime_type": "text/x-python"}},
    )
    telegram_file = AsyncMock()
    telegram_file.download_as_bytearray = AsyncMock(return_value=bytearray(b"x = 1"))
    ctx.bot.get_file = AsyncMock(return_value=telegram_file)

    result = await _call(_tool(ctx, "read_message"), message_id=10)

    assert result.attachments == []
    assert '<file name="a.py" from="message #10">\nx = 1\n</file>' in result.text


@pytest.mark.asyncio
@patch("src.bot.handlers.ai_tools.ai_history")
@patch("src.bot.handlers.ai_tools.message_dao")
async def test_read_message_bot_response(mock_message_dao, mock_history, ctx):
    mock_message_dao.get_message.return_value = None
    mock_history.find_ai_exchange.return_value = MagicMock(metadata={"bot_response": "yes"})

    result = await _call(_tool(ctx, "read_message"), message_id=50)

    assert result.text == "[#50] Chaddi (you): yes"


@pytest.mark.asyncio
@patch("src.bot.handlers.ai_tools.ai_history")
@patch("src.bot.handlers.ai_tools.message_dao")
async def test_read_message_not_found(mock_message_dao, mock_history, ctx):
    mock_message_dao.get_message.return_value = None
    mock_history.find_ai_exchange.return_value = None

    result = await _call(_tool(ctx, "read_message"), message_id=50)

    assert "not found" in result.text


# --- fetch_url --------------------------------------------------------------


def _resolve_to(address):
    return lambda host, port: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, port))]


@pytest.mark.parametrize(
    "url, address, error",
    [
        ("ftp://example.com/x", "93.184.216.34", "only http"),
        ("http:///nohost", "93.184.216.34", "no host"),
        ("http://localhost:8080", "127.0.0.1", "private"),
        ("http://router.lan", "192.168.1.1", "private"),
        ("http://metadata", "169.254.169.254", "private"),
        ("http://v6.example", "::1", "private"),
    ],
)
def test_check_public_url_rejects(url, address, error):
    with (
        patch("src.bot.handlers.ai_tools.socket.getaddrinfo", side_effect=_resolve_to(address)),
        pytest.raises(ValueError, match=error),
    ):
        ai_tools.check_public_url(url)


def test_check_public_url_allows_public():
    with patch(
        "src.bot.handlers.ai_tools.socket.getaddrinfo", side_effect=_resolve_to("93.184.216.34")
    ):
        ai_tools.check_public_url("https://example.com/page")


def _response(status=200, headers=None, body=b"", is_redirect=False):
    response = MagicMock()
    response.status_code = status
    response.headers = headers or {}
    response.is_redirect = is_redirect
    response.iter_content.return_value = [body]
    return response


@patch("src.bot.handlers.ai_tools.check_public_url")
@patch("src.bot.handlers.ai_tools.requests.get")
def test_fetch_url_follows_redirects_and_checks_each_hop(mock_get, mock_check):
    mock_get.side_effect = [
        _response(301, {"location": "/next"}, is_redirect=True),
        _response(200, {"content-type": "text/html; charset=utf-8"}, b"<p>hi</p>"),
    ]

    final_url, content_type, body, truncated = ai_tools.fetch_url("https://example.com/start")

    assert final_url == "https://example.com/next"
    assert content_type == "text/html"
    assert body == b"<p>hi</p>"
    assert truncated is False
    assert [c.args[0] for c in mock_check.call_args_list] == [
        "https://example.com/start",
        "https://example.com/next",
    ]
    assert mock_get.call_args.kwargs["allow_redirects"] is False


@patch("src.bot.handlers.ai_tools.check_public_url")
@patch("src.bot.handlers.ai_tools.requests.get")
def test_fetch_url_caps_size_and_errors(mock_get, mock_check):
    mock_get.return_value = _response(
        200, {"content-type": "text/plain"}, b"x" * (ai_tools.FETCH_MAX_BYTES + 5)
    )
    _, _, body, truncated = ai_tools.fetch_url("https://example.com")
    assert len(body) == ai_tools.FETCH_MAX_BYTES
    assert truncated is True

    mock_get.return_value = _response(404)
    with pytest.raises(ValueError, match="404"):
        ai_tools.fetch_url("https://example.com")

    mock_get.return_value = _response(302, {"location": "/loop"}, is_redirect=True)
    with pytest.raises(ValueError, match="too many redirects"):
        ai_tools.fetch_url("https://example.com")


def test_html_to_text():
    title, text = ai_tools.html_to_text(
        "<html><head><title> The  Title </title><style>p{}</style></head>"
        "<body><script>evil()</script><h1>Heading</h1><p>Para   one</p><div>two</div></body></html>"
    )
    assert title == "The Title"
    assert text == "Heading\nPara one\ntwo"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "content_type, body, expected, attached",
    [
        ("text/html", b"<title>T</title><p>Hello</p>", "URL: https://x.com\nTitle: T\n\nHello", 0),
        ("application/json", b'{"a": 1}', 'URL: https://x.com\n\n{"a": 1}', 0),
        ("image/png", b"png", "Fetched https://x.com - the image is attached.", 1),
        ("application/pdf", b"%PDF", "Fetched https://x.com - the PDF is attached.", 1),
        ("application/zip", b"PK", "Can't read https://x.com - unsupported content type", 0),
    ],
)
async def test_fetch_url_tool(content_type, body, expected, attached):
    with patch(
        "src.bot.handlers.ai_tools.fetch_url",
        return_value=("https://x.com", content_type, body, False),
    ):
        result = await ai_tools.fetch_url_tool().handler(url="https://x.com")

    assert result.text.startswith(expected)
    assert len(result.attachments) == attached
    assert ai_tools.fetch_url_tool().describe({"url": "https://x.com/a"}) == "🌐 opening x.com…"


# --- set_reminder -----------------------------------------------------------


@pytest.fixture
def remind():
    with patch("src.bot.handlers.ai_tools.remind") as mock_remind:
        mock_remind.has_too_many_reminders.return_value = False
        mock_remind.schedule_reminder.return_value = MagicMock(job_id=7)
        yield mock_remind


def test_set_reminder_with_delay(ctx, remind):
    result = _tool(ctx, "set_reminder").handler(message="chai", delay_minutes=30)

    assert result.startswith("Reminder #7 set for")
    kwargs = remind.schedule_reminder.call_args.kwargs
    assert kwargs["chat_id"] == 456
    assert kwargs["from_bakchod_id"] == 123
    assert kwargs["reply_to_message_id"] == 789
    assert kwargs["reminder_message"] == "chai"
    assert 1790 <= kwargs["due_seconds"] <= 1800
    assert remind.schedule_reminder.call_args.args == (ctx.job_queue,)


def test_set_reminder_at_time(ctx, remind):
    at = (datetime.now() + timedelta(days=1)).replace(microsecond=0)

    _tool(ctx, "set_reminder").handler(message="turf", remind_at=at.isoformat())

    due = remind.schedule_reminder.call_args.kwargs["due_seconds"]
    assert 86390 <= due <= 86400


@pytest.mark.parametrize(
    "kwargs, error",
    [
        ({}, "pass delay_minutes or remind_at"),
        ({"delay_minutes": 0}, "between a minute and a year"),
        ({"delay_minutes": 60 * 24 * 400}, "between a minute and a year"),
    ],
)
def test_set_reminder_validation(ctx, remind, kwargs, error):
    assert error in _tool(ctx, "set_reminder").handler(message="x", **kwargs)
    assert not remind.schedule_reminder.called


def test_set_reminder_caps(ctx, remind):
    tool = _tool(ctx, "set_reminder")
    for _ in range(ai_tools.MAX_REMINDERS_PER_REQUEST):
        tool.handler(message="x", delay_minutes=5)
    assert "at most" in tool.handler(message="x", delay_minutes=5)

    ctx.reminders_set = 0
    remind.has_too_many_reminders.return_value = True
    assert "too many pending" in tool.handler(message="x", delay_minutes=5)


# --- generate_image ---------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_image(ctx):
    image = LLMAttachment(b"png", "image/png")
    with (
        patch("src.bot.handlers.ai_tools.util.paywall_user", return_value=True) as paywall,
        patch("src.bot.handlers.ai_tools.ai.generate_image", new=AsyncMock(return_value=image)),
    ):
        tool = _tool(ctx, "generate_image")
        result = await tool.handler(prompt="a cat in a chaddi")
        second = await tool.handler(prompt="another")

    paywall.assert_called_once_with(123, ai_tools.IMAGE_COST)
    kwargs = ctx.bot.send_photo.call_args.kwargs
    assert kwargs["photo"] == b"png"
    assert kwargs["caption"] == "a cat in a chaddi"
    assert kwargs["reply_parameters"].message_id == 789
    assert "message #900" in result
    assert "at most" in second


@pytest.mark.asyncio
async def test_generate_image_needs_rokda(ctx):
    with patch("src.bot.handlers.ai_tools.util.paywall_user", return_value=False):
        result = await _tool(ctx, "generate_image").handler(prompt="a cat")

    assert "doesn't have the 500" in result
    assert not ctx.bot.send_photo.called


@pytest.mark.asyncio
async def test_generate_image_refunds_on_failure(ctx):
    with (
        patch("src.bot.handlers.ai_tools.util.paywall_user", return_value=True),
        patch(
            "src.bot.handlers.ai_tools.ai.generate_image",
            new=AsyncMock(side_effect=RuntimeError("no credits")),
        ),
        patch("src.bot.handlers.ai_tools.Bakchod") as mock_bakchod,
    ):
        mock_bakchod.get_by_id.return_value.rokda = 100
        with pytest.raises(RuntimeError):
            await _tool(ctx, "generate_image").handler(prompt="a cat")

    assert mock_bakchod.get_by_id.return_value.rokda == 100 + ai_tools.IMAGE_COST
    assert ctx.images_generated == 0


# --- create_poll ------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_poll(ctx):
    tool = _tool(ctx, "create_poll")
    result = await tool.handler(question="Chai or coffee?", options=["chai", " coffee ", ""])

    kwargs = ctx.bot.send_poll.call_args.kwargs
    assert kwargs["options"] == ["chai", "coffee"]
    assert kwargs["is_anonymous"] is False
    assert kwargs["reply_parameters"].message_id == 789
    assert "message #901" in result
    assert "at most" in await tool.handler(question="again?", options=["a", "b"])


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "question, options, error",
    [("q", ["only one"], "between 2 and 10"), ("q", list("abcdefghijk"), "between 2 and 10")],
)
async def test_create_poll_validation(ctx, question, options, error):
    assert error in await _tool(ctx, "create_poll").handler(question=question, options=options)
    assert not ctx.bot.send_poll.called


@pytest.mark.asyncio
async def test_create_poll_needs_question(ctx):
    assert "empty" in await _tool(ctx, "create_poll").handler(question=" ", options=["a", "b"])


# --- Memory -----------------------------------------------------------------


@patch("src.bot.handlers.ai_tools.ai_history")
def test_remember_and_forget(mock_history, ctx):
    mock_history.add_memory.return_value = {"id": 3}
    mock_history.remove_memory.side_effect = [{"text": "likes chai"}, None]

    assert _tool(ctx, "remember").handler(note="likes chai", about="@minji") == "Saved as note [3]."
    mock_history.add_memory.assert_called_once_with(456, "likes chai", "@minji", added_by="@arkits")
    assert _tool(ctx, "forget").handler(note_id=3) == "Forgot note [3]: likes chai"
    assert _tool(ctx, "forget").handler(note_id=4) == "There's no note [4]."


@patch("src.bot.handlers.ai_tools.ai_history")
def test_remember_errors_and_budget(mock_history, ctx):
    mock_history.add_memory.side_effect = ValueError("memory is full")
    assert _tool(ctx, "remember").handler(note="x") == "Error: memory is full"

    ctx.memory_changes = ai_tools.MAX_MEMORY_CHANGES_PER_REQUEST
    assert "at most" in _tool(ctx, "remember").handler(note="x")
    assert "at most" in _tool(ctx, "forget").handler(note_id=1)


def test_every_tool_has_a_status(ctx):
    for tool in ai_tools.build_tools(ctx):
        assert tool.describe({"url": "https://x.com", "message_id": 1}), tool.name
        assert isinstance(tool.parameters, dict)
