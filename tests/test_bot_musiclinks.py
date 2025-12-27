from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Message, Update
from telegram.ext import ContextTypes

from src.bot.handlers import musiclinks


@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    return update


@pytest.fixture
def mock_context():
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    return context


@pytest.mark.asyncio
async def test_handle_no_message_text(mock_update, mock_context):
    """Test handler with no message text"""
    mock_update.message.text = None

    await musiclinks.handle(mock_update, mock_context)

    assert not mock_update.message.reply_text.called


@pytest.mark.asyncio
async def test_handle_no_music_url(mock_update, mock_context):
    """Test handler with text but no music URL"""
    mock_update.message.text = "Just a regular message without any music links"

    await musiclinks.handle(mock_update, mock_context)

    assert not mock_update.message.reply_text.called


@pytest.mark.asyncio
@patch("src.bot.handlers.musiclinks.httpx.AsyncClient")
async def test_handle_spotify_url(mock_async_client, mock_update, mock_context):
    """Test handler with Spotify URL"""
    mock_update.message.text = "Check out this song: https://open.spotify.com/track/123"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "linksByPlatform": {
            "spotify": {"url": "https://open.spotify.com/track/123"},
            "appleMusic": {"url": "https://music.apple.com/album/123"},
            "youtube": {"url": "https://www.youtube.com/watch?v=abc"},
        }
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_async_client.return_value.__aenter__.return_value = mock_client

    await musiclinks.handle(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args
    assert "Spotify" in call_args[0][0]
    assert "Apple Music" in call_args[0][0]


@pytest.mark.asyncio
@patch("src.bot.handlers.musiclinks.httpx.AsyncClient")
async def test_handle_youtube_url(mock_async_client, mock_update, mock_context):
    """Test handler with YouTube URL"""
    mock_update.message.text = "Watch this: https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "linksByPlatform": {
            "youtube": {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            "youtubeMusic": {"url": "https://music.youtube.com/watch?v=dQw4w9WgXcQ"},
        }
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_async_client.return_value.__aenter__.return_value = mock_client

    await musiclinks.handle(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args
    assert "YouTube" in call_args[0][0]


@pytest.mark.asyncio
@patch("src.bot.handlers.musiclinks.httpx.AsyncClient")
async def test_handle_apple_music_url(mock_async_client, mock_update, mock_context):
    """Test handler with Apple Music URL"""
    mock_update.message.text = "Listen here: https://music.apple.com/us/album/test/123"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "linksByPlatform": {
            "appleMusic": {"url": "https://music.apple.com/us/album/test/123"},
            "spotify": {"url": "https://open.spotify.com/track/123"},
        }
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_async_client.return_value.__aenter__.return_value = mock_client

    await musiclinks.handle(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args
    assert "Apple Music" in call_args[0][0]
    assert "Spotify" in call_args[0][0]


@pytest.mark.asyncio
@patch("src.bot.handlers.musiclinks.httpx.AsyncClient")
async def test_handle_api_error(mock_async_client, mock_update, mock_context):
    """Test handler when API returns error status"""
    mock_update.message.text = "https://open.spotify.com/track/123"

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_async_client.return_value.__aenter__.return_value = mock_client

    await musiclinks.handle(mock_update, mock_context)

    assert not mock_update.message.reply_text.called


@pytest.mark.asyncio
@patch("src.bot.handlers.musiclinks.httpx.AsyncClient")
async def test_handle_no_links_in_response(mock_async_client, mock_update, mock_context):
    """Test handler when API returns no links"""
    mock_update.message.text = "https://open.spotify.com/track/123"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"linksByPlatform": {}}

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_async_client.return_value.__aenter__.return_value = mock_client

    await musiclinks.handle(mock_update, mock_context)

    assert not mock_update.message.reply_text.called


@pytest.mark.asyncio
@patch("src.bot.handlers.musiclinks.httpx.AsyncClient")
async def test_handle_no_links_by_platform(mock_async_client, mock_update, mock_context):
    """Test handler when API returns no linksByPlatform key"""
    mock_update.message.text = "https://open.spotify.com/track/123"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_async_client.return_value.__aenter__.return_value = mock_client

    await musiclinks.handle(mock_update, mock_context)

    assert not mock_update.message.reply_text.called


@pytest.mark.asyncio
@patch("src.bot.handlers.musiclinks.httpx.AsyncClient")
async def test_handle_multiple_urls(mock_async_client, mock_update, mock_context):
    """Test handler with multiple music URLs - should only process first one"""
    mock_update.message.text = (
        "First: https://open.spotify.com/track/123 and second: https://music.apple.com/album/456"
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "linksByPlatform": {
            "spotify": {"url": "https://open.spotify.com/track/123"},
        }
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_async_client.return_value.__aenter__.return_value = mock_client

    await musiclinks.handle(mock_update, mock_context)

    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args
    # Should only call API with the first URL
    assert "open.spotify.com" in call_args[0][0]


@pytest.mark.asyncio
@patch("src.bot.handlers.musiclinks.httpx.AsyncClient")
async def test_handle_soundcloud_url(mock_async_client, mock_update, mock_context):
    """Test handler with SoundCloud URL"""
    mock_update.message.text = "Listen: https://www.soundcloud.com/artist/track"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "linksByPlatform": {
            "soundcloud": {"url": "https://www.soundcloud.com/artist/track"},
        }
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_async_client.return_value.__aenter__.return_value = mock_client

    await musiclinks.handle(mock_update, mock_context)

    # SoundCloud is commented out in the handler, so no reply should be sent
    assert not mock_update.message.reply_text.called


@pytest.mark.asyncio
@patch("src.bot.handlers.musiclinks.httpx.AsyncClient")
async def test_handle_exception(mock_async_client, mock_update, mock_context):
    """Test handler exception handling"""
    mock_update.message.text = "https://open.spotify.com/track/123"

    mock_client = AsyncMock()
    mock_client.get.side_effect = Exception("Network error")
    mock_async_client.return_value.__aenter__.return_value = mock_client

    await musiclinks.handle(mock_update, mock_context)

    assert not mock_update.message.reply_text.called


@pytest.mark.asyncio
@patch("src.bot.handlers.musiclinks.httpx.AsyncClient")
async def test_handle_deezer_url(mock_async_client, mock_update, mock_context):
    """Test handler with Deezer URL"""
    mock_update.message.text = "https://www.deezer.com/track/123"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "linksByPlatform": {
            "deezer": {"url": "https://www.deezer.com/track/123"},
        }
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_async_client.return_value.__aenter__.return_value = mock_client

    await musiclinks.handle(mock_update, mock_context)

    # Deezer is commented out in the handler, so no reply should be sent
    assert not mock_update.message.reply_text.called


@pytest.mark.asyncio
@patch("src.bot.handlers.musiclinks.httpx.AsyncClient")
async def test_handle_tidal_url(mock_async_client, mock_update, mock_context):
    """Test handler with Tidal URL"""
    mock_update.message.text = "https://listen.tidal.com/track/123"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "linksByPlatform": {
            "tidal": {"url": "https://listen.tidal.com/track/123"},
        }
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_async_client.return_value.__aenter__.return_value = mock_client

    await musiclinks.handle(mock_update, mock_context)

    # Tidal is commented out in the handler, so no reply should be sent
    assert not mock_update.message.reply_text.called


@pytest.mark.asyncio
@patch("src.bot.handlers.musiclinks.httpx.AsyncClient")
async def test_handle_youtube_music_url(mock_async_client, mock_update, mock_context):
    """Test handler with YouTube Music URL"""
    mock_update.message.text = "https://music.youtube.com/watch?v=abc123"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "linksByPlatform": {
            "youtubeMusic": {"url": "https://music.youtube.com/watch?v=abc123"},
            "spotify": {"url": "https://open.spotify.com/track/123"},
        }
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_async_client.return_value.__aenter__.return_value = mock_client

    await musiclinks.handle(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args
    assert "YouTube Music" in call_args[0][0]


@pytest.mark.asyncio
@patch("src.bot.handlers.musiclinks.httpx.AsyncClient")
async def test_handle_youtu_be_short_url(mock_async_client, mock_update, mock_context):
    """Test handler with youtu.be short URL"""
    mock_update.message.text = "https://youtu.be/dQw4w9WgXcQ"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "linksByPlatform": {
            "youtube": {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        }
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_async_client.return_value.__aenter__.return_value = mock_client

    await musiclinks.handle(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()


@pytest.mark.asyncio
@patch("src.bot.handlers.musiclinks.httpx.AsyncClient")
async def test_handle_reply_with_correct_format(mock_async_client, mock_update, mock_context):
    """Test that reply has correct format with Markdown"""
    mock_update.message.text = "https://open.spotify.com/track/123"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "linksByPlatform": {
            "spotify": {"url": "https://open.spotify.com/track/123"},
            "appleMusic": {"url": "https://music.apple.com/album/123"},
        }
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_async_client.return_value.__aenter__.return_value = mock_client

    await musiclinks.handle(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args
    assert call_args[1]["parse_mode"] == "Markdown"
    assert call_args[1]["disable_web_page_preview"] is True


@pytest.mark.asyncio
@patch("src.bot.handlers.musiclinks.httpx.AsyncClient")
async def test_handle_platform_with_missing_url(mock_async_client, mock_update, mock_context):
    """Test handler when platform exists but URL is missing"""
    mock_update.message.text = "https://open.spotify.com/track/123"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "linksByPlatform": {
            "spotify": {},  # Missing URL
            "appleMusic": {"url": "https://music.apple.com/album/123"},
        }
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_async_client.return_value.__aenter__.return_value = mock_client

    await musiclinks.handle(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args
    # Should still reply with available links
    assert "Apple Music" in call_args[0][0]
    assert "Spotify" not in call_args[0][0]
