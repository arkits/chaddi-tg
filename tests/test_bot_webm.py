from unittest.mock import MagicMock

import pytest
from telegram import Document, Message, Update, User
from telegram.ext import ContextTypes

from src.bot.handlers import webm


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
async def test_handle_no_document(mock_update, mock_context):
    """Test handler with no document"""
    mock_update.message.document = None

    await webm.handle(mock_update, mock_context)

    assert not mock_update.message.reply_text.called


@pytest.mark.asyncio
async def test_handle_no_file_name(mock_update, mock_context):
    """Test handler with document but no file name"""
    mock_document = MagicMock(spec=Document)
    mock_document.file_name = None
    mock_update.message.document = mock_document

    await webm.handle(mock_update, mock_context)

    assert not mock_update.message.reply_text.called


@pytest.mark.asyncio
async def test_handle_not_webm_file(mock_update, mock_context):
    """Test handler with non-webm file"""
    mock_document = MagicMock(spec=Document)
    mock_document.file_name = "video.mp4"
    mock_update.message.document = mock_document

    await webm.handle(mock_update, mock_context)

    assert not mock_update.message.reply_text.called


def test_build_webm_conversion_response_basic():
    """Test build_webm_conversion_response with basic parameters"""
    result = webm.build_webm_conversion_response("John", "1 minute", "video.webm", None)

    assert "John" in result
    assert "video.webm" in result
    assert "1 minute" in result
