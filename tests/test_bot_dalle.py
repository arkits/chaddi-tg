from unittest.mock import MagicMock, patch

import pytest
from telegram import Message, Update, User
from telegram.ext import ContextTypes

from src.bot.handlers import dalle


@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.from_user = MagicMock(spec=User)
    return update


@pytest.fixture
def mock_context():
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    return context


@pytest.mark.asyncio
async def test_handle_no_from_user(mock_update, mock_context):
    """Test handler when from_user is None"""
    mock_update.message.from_user = None

    await dalle.handle(mock_update, mock_context)

    assert not mock_update.message.reply_text.called


@pytest.mark.asyncio
@patch("src.bot.handlers.dalle.bakchod_dao.get_or_create_bakchod_from_tg_user")
async def test_handle_dalle_disabled_for_bakchod(mock_get_bakchod, mock_update, mock_context):
    """Test handler when dalle is disabled for user"""
    mock_bakchod = MagicMock()
    mock_bakchod.metadata = {}
    mock_bakchod.pretty_name = "Test User"
    mock_bakchod.tg_id = 123
    mock_get_bakchod.return_value = mock_bakchod
    mock_update.message.text = "/dalle a test prompt"
    mock_update.message.from_user.id = 123

    await dalle.handle(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args
    assert "not enabled" in call_args[0][0]


@pytest.mark.asyncio
@patch("src.bot.handlers.dalle.bakchod_dao.get_or_create_bakchod_from_tg_user")
async def test_handle_short_prompt(mock_get_bakchod, mock_update, mock_context):
    """Test handler with prompt too short"""
    mock_bakchod = MagicMock()
    mock_bakchod.metadata = {"dalle": True}
    mock_get_bakchod.return_value = mock_bakchod
    mock_update.message.text = "/dalle abc"
    mock_update.message.from_user.id = 123

    await dalle.handle(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args
    assert "longer prompt" in call_args[0][0]


def test_extract_prompt_with_command():
    """Test extract_prompt with /dalle command"""
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.text = "/dalle A beautiful landscape"

    result = dalle.extract_prompt(update)

    assert result == "A beautiful landscape"


def test_extract_prompt_without_command():
    """Test extract_prompt without /dalle prefix"""
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.text = "A beautiful landscape"

    result = dalle.extract_prompt(update)

    assert result == "A beautiful landscape"


def test_extract_prompt_with_extra_spaces():
    """Test extract_prompt with extra spaces"""
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.text = "/dalle   A beautiful landscape   "

    result = dalle.extract_prompt(update)

    assert result == "A beautiful landscape"
