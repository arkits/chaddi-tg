from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import Message, Update
from telegram.ext import ContextTypes

from src.bot.handlers import x_links


@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture
def mock_context():
    return MagicMock(spec=ContextTypes.DEFAULT_TYPE)


@pytest.mark.asyncio
async def test_handle_no_message_text(mock_update, mock_context):
    mock_update.message.text = None

    await x_links.handle(mock_update, mock_context)

    mock_update.message.reply_text.assert_not_awaited()


@pytest.mark.asyncio
async def test_handle_no_x_url(mock_update, mock_context):
    mock_update.message.text = "See https://example.com and https://twitter.com/chaddibot"

    await x_links.handle(mock_update, mock_context)

    mock_update.message.reply_text.assert_not_awaited()


@pytest.mark.asyncio
async def test_handle_x_url(mock_update, mock_context):
    mock_update.message.text = "See https://x.com/chaddibot/status/123?s=20"

    await x_links.handle(mock_update, mock_context)

    mock_update.message.reply_text.assert_awaited_once_with(
        "http://xcancel.com/chaddibot/status/123?s=20"
    )


@pytest.mark.asyncio
async def test_handle_www_x_url_case_insensitively(mock_update, mock_context):
    mock_update.message.text = "See HTTP://WWW.X.COM/chaddibot/status/123"

    await x_links.handle(mock_update, mock_context)

    mock_update.message.reply_text.assert_awaited_once_with(
        "http://xcancel.com/chaddibot/status/123"
    )


@pytest.mark.asyncio
async def test_handle_trailing_sentence_punctuation(mock_update, mock_context):
    mock_update.message.text = "See this (https://x.com/chaddibot/status/123)."

    await x_links.handle(mock_update, mock_context)

    mock_update.message.reply_text.assert_awaited_once_with(
        "http://xcancel.com/chaddibot/status/123"
    )


@pytest.mark.asyncio
async def test_handle_does_not_match_x_subdomain_or_lookalike(mock_update, mock_context):
    mock_update.message.text = "https://not.x.com/post https://x.com.example.com/post"

    await x_links.handle(mock_update, mock_context)

    mock_update.message.reply_text.assert_not_awaited()


@pytest.mark.asyncio
async def test_handle_only_first_x_url(mock_update, mock_context):
    mock_update.message.text = "https://x.com/first/status/1 https://x.com/second/status/2"

    await x_links.handle(mock_update, mock_context)

    mock_update.message.reply_text.assert_awaited_once_with("http://xcancel.com/first/status/1")
