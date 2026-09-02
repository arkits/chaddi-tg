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


def test_handler_is_disabled():
    assert x_links.ENABLED is False


@pytest.mark.asyncio
async def test_handle_does_not_reply_while_disabled(mock_update, mock_context):
    mock_update.message.text = "See https://x.com/chaddibot/status/123?s=20"

    await x_links.handle(mock_update, mock_context)

    mock_update.message.reply_text.assert_not_awaited()
