from unittest.mock import MagicMock, patch

import pytest
from telegram import Chat, Message, User

from src.bot.handlers import weather


@pytest.fixture
def mock_update():
    """Create a mock Telegram Update object for testing."""
    user = MagicMock(spec=User)
    user.id = 123456
    user.username = "testuser"
    user.first_name = "Test"

    chat = MagicMock(spec=Chat)
    chat.id = -1001234567890
    chat.type = "group"

    message = MagicMock(spec=Message)
    message.message_id = 1
    message.from_user = user
    message.chat = chat
    message.text = "/weather Mumbai"
    message.reply_to_message = None
    message.caption = None

    context = MagicMock()
    context.args = ["Mumbai"]

    update = MagicMock()
    update.message = message

    return update, context


class TestWeather:
    @patch("src.bot.handlers.weather.requests")
    @patch("src.bot.handlers.weather.bakchod_dao")
    @patch("src.bot.handlers.weather.dc")
    @pytest.mark.anyio
    async def test_handle_success_with_args(
        self, mock_dc, mock_bakchod_dao, mock_requests, mock_update
    ):
        """Test weather handler success case with location in args."""
        update, context = mock_update

        mock_bakchod = MagicMock()
        mock_bakchod.metadata = None
        mock_bakchod_dao.get_bakchod_from_update.return_value = mock_bakchod

        sent_message = MagicMock()
        update.message.reply_text.return_value = sent_message

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "weather": [{"description": "clear sky"}],
            "main": {"temp": 30.0, "humidity": 65},
            "wind": {"speed": 5.0},
            "name": "Mumbai",
            "coord": {"lat": 19.0760, "lon": 72.8777},
        }
        mock_requests.get.return_value = mock_response
        mock_requests.exceptions.HTTPError = Exception

        mock_aqi_response = MagicMock()
        mock_aqi_response.status_code = 200
        mock_aqi_response.json.return_value = {"list": [{"main": {"aqi": 2}}]}
        mock_requests.get.side_effect = [mock_response, mock_aqi_response]

        await weather.handle(update, context)

        mock_dc.log_command_usage.assert_called_once_with("weather", update)

    @patch("src.bot.handlers.weather.bakchod_dao")
    @patch("src.bot.handlers.weather.dc")
    @pytest.mark.anyio
    async def test_handle_no_location(self, mock_dc, mock_bakchod_dao, mock_update):
        """Test weather handler without location."""
        update, context = mock_update
        context.args = None
        update.message.reply_to_message = None
        update.message.caption = None

        mock_bakchod = MagicMock()
        mock_bakchod.metadata = {}
        mock_bakchod_dao.get_bakchod_from_update.return_value = mock_bakchod

        await weather.handle(update, context)

        mock_dc.log_command_usage.assert_called_once_with("weather", update)
        update.message.reply_text.assert_called_once()
        assert "provide a location" in update.message.reply_text.call_args[0][0]

    @patch("src.bot.handlers.weather.bakchod_dao")
    @patch("src.bot.handlers.weather.dc")
    @pytest.mark.anyio
    async def test_handle_saved_location(self, mock_dc, mock_bakchod_dao, mock_update):
        """Test weather handler with saved location in metadata."""
        update, context = mock_update
        context.args = None
        update.message.reply_to_message = None
        update.message.caption = None

        mock_bakchod = MagicMock()
        mock_bakchod.metadata = {"last_weather_location": "Delhi"}
        mock_bakchod_dao.get_bakchod_from_update.return_value = mock_bakchod

        await weather.handle(update, context)

        mock_dc.log_command_usage.assert_called_once_with("weather", update)

    @patch("src.bot.handlers.weather.bakchod_dao")
    @patch("src.bot.handlers.weather.dc")
    @pytest.mark.anyio
    async def test_get_fallback_description_rain(self, mock_dc, mock_bakchod_dao):
        """Test _get_fallback_description with rain."""
        result = weather._get_fallback_description("light rain")

        assert "rain" in result.lower() or "leaking" in result.lower()

    @patch("src.bot.handlers.weather.bakchod_dao")
    @patch("src.bot.handlers.weather.dc")
    @pytest.mark.anyio
    async def test_get_fallback_description_sunny(self, mock_dc, mock_bakchod_dao):
        """Test _get_fallback_description with sunny weather."""
        result = weather._get_fallback_description("sunny")

        assert isinstance(result, str)
        assert len(result) > 0

    @patch("src.bot.handlers.weather.bakchod_dao")
    @patch("src.bot.handlers.weather.dc")
    @pytest.mark.anyio
    async def test_get_fallback_description_unknown(self, mock_dc, mock_bakchod_dao):
        """Test _get_fallback_description with unknown weather."""
        result = weather._get_fallback_description("weird weather")

        assert isinstance(result, str)
        assert len(result) > 0
        assert "weird weather" in result
