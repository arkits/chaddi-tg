from unittest.mock import MagicMock, patch

import pytest
from telegram import Message, Update, User
from telegram.ext import ContextTypes

from src.bot.handlers import sutta


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

    await sutta.handle(mock_update, mock_context)

    assert not mock_update.message.reply_text.called


@pytest.mark.asyncio
@patch("src.bot.handlers.sutta.util.paywall_user")
async def test_handle_insufficient_rokda(mock_paywall, mock_update, mock_context):
    """Test handler with insufficient rokda"""
    mock_paywall.return_value = False
    mock_update.message.from_user.id = 123

    await sutta.handle(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args
    assert "don't have enough" in call_args[0][0]


@pytest.mark.asyncio
@patch("src.bot.handlers.sutta.Bakchod")
@patch("src.bot.handlers.sutta.util.paywall_user")
async def test_handle_existing_sutta_job(
    mock_paywall, mock_bakchod_class, mock_update, mock_context
):
    """Test handler when user already has a running sutta job"""
    mock_paywall.return_value = True
    mock_update.message.from_user.id = 123

    mock_bakchod = MagicMock()
    mock_bakchod.metadata = {"sutta_ittr": 5}
    mock_bakchod_class.get_by_id.return_value = mock_bakchod

    await sutta.handle(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args
    assert "DHUMRAPAN" in call_args[0][0]


@pytest.mark.asyncio
@patch("src.bot.handlers.sutta.Bakchod")
async def test_update_sutta_in_range(mock_bakchod_class, mock_context):
    """Test update_sutta for iterations 0-8"""
    mock_bakchod = MagicMock()
    mock_bakchod.metadata = {"sutta_ittr": 3}
    mock_bakchod.save = MagicMock()

    with patch("src.bot.handlers.sutta.Bakchod") as mock_bakchod_class:
        mock_bakchod_class.get_by_id.return_value = mock_bakchod

        mock_job = MagicMock()
        mock_job.data = {"chat_id": 123, "message_id": 456, "bakchod_id": 789}
        mock_context = MagicMock()
        mock_context.job = mock_job

        await sutta.update_sutta(mock_context)

        mock_context.bot.edit_message_text.assert_called_once()
