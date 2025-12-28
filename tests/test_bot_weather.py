from unittest.mock import MagicMock, patch

import pytest
import requests
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

    @patch("src.bot.handlers.weather.requests")
    @patch("src.bot.handlers.weather.bakchod_dao")
    @patch("src.bot.handlers.weather.dc")
    @pytest.mark.anyio
    async def test_handle_saved_location(
        self, mock_dc, mock_bakchod_dao, mock_requests, mock_update
    ):
        """Test weather handler with saved location in metadata."""
        update, context = mock_update
        context.args = None
        update.message.reply_to_message = None
        update.message.caption = None

        mock_bakchod = MagicMock()
        mock_bakchod.metadata = {"last_weather_location": "Delhi"}
        mock_bakchod_dao.get_bakchod_from_update.return_value = mock_bakchod

        sent_message = MagicMock()
        update.message.reply_text.return_value = sent_message

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "weather": [{"description": "clear sky"}],
            "main": {"temp": 28.0, "humidity": 60},
            "wind": {"speed": 4.5},
            "name": "Delhi",
            "coord": {"lat": 28.7041, "lon": 77.1025},
        }
        mock_requests.get.return_value = mock_response
        mock_requests.exceptions.HTTPError = Exception

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

    @patch("src.bot.handlers.weather.requests")
    @patch("src.bot.handlers.weather.bakchod_dao")
    @patch("src.bot.handlers.weather.dc")
    @pytest.mark.anyio
    async def test_handle_location_from_reply_text(
        self, mock_dc, mock_bakchod_dao, mock_requests, mock_update
    ):
        """Test weather handler with location from reply message text."""
        update, context = mock_update
        context.args = None
        update.message.text = "/weather"

        reply_message = MagicMock()
        reply_message.text = "London"
        reply_message.caption = None
        update.message.reply_to_message = reply_message

        mock_bakchod = MagicMock()
        mock_bakchod.metadata = None
        mock_bakchod_dao.get_bakchod_from_update.return_value = mock_bakchod

        sent_message = MagicMock()
        update.message.reply_text.return_value = sent_message

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "weather": [{"description": "cloudy"}],
            "main": {"temp": 15.0, "humidity": 70},
            "wind": {"speed": 3.5},
            "name": "London",
            "coord": {"lat": 51.5074, "lon": -0.1278},
        }
        mock_requests.get.return_value = mock_response
        mock_requests.exceptions.HTTPError = Exception

        await weather.handle(update, context)

        mock_dc.log_command_usage.assert_called_once_with("weather", update)

    @patch("src.bot.handlers.weather.requests")
    @patch("src.bot.handlers.weather.bakchod_dao")
    @patch("src.bot.handlers.weather.dc")
    @pytest.mark.anyio
    async def test_handle_location_from_reply_caption(
        self, mock_dc, mock_bakchod_dao, mock_requests, mock_update
    ):
        """Test weather handler with location from reply message caption."""
        update, context = mock_update
        context.args = None
        update.message.text = "/weather"

        reply_message = MagicMock()
        reply_message.text = None
        reply_message.caption = "Paris"
        update.message.reply_to_message = reply_message

        mock_bakchod = MagicMock()
        mock_bakchod.metadata = None
        mock_bakchod_dao.get_bakchod_from_update.return_value = mock_bakchod

        sent_message = MagicMock()
        update.message.reply_text.return_value = sent_message

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "weather": [{"description": "partly cloudy"}],
            "main": {"temp": 18.0, "humidity": 60},
            "wind": {"speed": 4.0},
            "name": "Paris",
            "coord": {"lat": 48.8566, "lon": 2.3522},
        }
        mock_requests.get.return_value = mock_response
        mock_requests.exceptions.HTTPError = Exception

        await weather.handle(update, context)

        mock_dc.log_command_usage.assert_called_once_with("weather", update)

    @patch("src.bot.handlers.weather.requests")
    @patch("src.bot.handlers.weather.bakchod_dao")
    @patch("src.bot.handlers.weather.dc")
    @pytest.mark.anyio
    async def test_handle_location_from_message_caption(
        self, mock_dc, mock_bakchod_dao, mock_requests, mock_update
    ):
        """Test weather handler with location from message caption."""
        update, context = mock_update
        context.args = None
        update.message.text = None
        update.message.caption = "Berlin"
        update.message.reply_to_message = None

        mock_bakchod = MagicMock()
        mock_bakchod.metadata = None
        mock_bakchod_dao.get_bakchod_from_update.return_value = mock_bakchod

        sent_message = MagicMock()
        update.message.reply_text.return_value = sent_message

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "weather": [{"description": "overcast"}],
            "main": {"temp": 10.0, "humidity": 80},
            "wind": {"speed": 2.5},
            "name": "Berlin",
            "coord": {"lat": 52.5200, "lon": 13.4050},
        }
        mock_requests.get.return_value = mock_response
        mock_requests.exceptions.HTTPError = Exception

        await weather.handle(update, context)

        mock_dc.log_command_usage.assert_called_once_with("weather", update)

    @patch("src.bot.handlers.weather.bakchod_dao")
    @patch("src.bot.handlers.weather.dc")
    @pytest.mark.anyio
    async def test_handle_no_api_key(self, mock_dc, mock_bakchod_dao, mock_update):
        """Test weather handler when API key is not configured."""
        update, context = mock_update
        context.args = ["TestLocation"]

        mock_bakchod = MagicMock()
        mock_bakchod.metadata = None
        mock_bakchod_dao.get_bakchod_from_update.return_value = mock_bakchod

        with patch("src.bot.handlers.weather.WEATHER_API_KEY", None):
            await weather.handle(update, context)

        mock_dc.log_command_usage.assert_called_once_with("weather", update)
        update.message.reply_text.assert_called_once()
        assert "API key is not configured" in update.message.reply_text.call_args[0][0]

    @pytest.mark.anyio
    async def test_handle_location_not_found(self, mock_update):
        """Test weather handler when location is not found (404)."""
        update, context = mock_update

        mock_bakchod = MagicMock()
        mock_bakchod.metadata = None

        sent_message = MagicMock()
        update.message.reply_text.return_value = sent_message

        http_error = requests.exceptions.HTTPError()
        http_error.response = MagicMock()
        http_error.response.status_code = 404

        with (
            patch("src.bot.handlers.weather.WEATHER_API_KEY", "test_key"),
            patch(
                "src.bot.handlers.weather.bakchod_dao.get_bakchod_from_update",
                return_value=mock_bakchod,
            ),
            patch("src.bot.handlers.weather.dc"),
            patch("src.bot.handlers.weather.requests.get", side_effect=http_error),
        ):
            await weather.handle(update, context)

        sent_message.edit_text.assert_called_once()
        assert "not found" in sent_message.edit_text.call_args[0][0]

    @pytest.mark.anyio
    async def test_handle_http_error(self, mock_update):
        """Test weather handler when HTTP error occurs."""
        update, context = mock_update

        mock_bakchod = MagicMock()
        mock_bakchod.metadata = None

        sent_message = MagicMock()
        update.message.reply_text.return_value = sent_message

        http_error = requests.exceptions.HTTPError()
        http_error.response = MagicMock()
        http_error.response.status_code = 500

        with (
            patch("src.bot.handlers.weather.WEATHER_API_KEY", "test_key"),
            patch(
                "src.bot.handlers.weather.bakchod_dao.get_bakchod_from_update",
                return_value=mock_bakchod,
            ),
            patch("src.bot.handlers.weather.dc"),
            patch("src.bot.handlers.weather.requests.get", side_effect=http_error),
        ):
            await weather.handle(update, context)

        sent_message.edit_text.assert_called_once()

    @pytest.mark.anyio
    async def test_handle_request_exception(self, mock_update):
        """Test weather handler when request exception occurs."""
        update, context = mock_update

        mock_bakchod = MagicMock()
        mock_bakchod.metadata = None

        sent_message = MagicMock()
        update.message.reply_text.return_value = sent_message

        request_exception = requests.exceptions.RequestException("Connection error")

        with (
            patch("src.bot.handlers.weather.WEATHER_API_KEY", "test_key"),
            patch(
                "src.bot.handlers.weather.bakchod_dao.get_bakchod_from_update",
                return_value=mock_bakchod,
            ),
            patch("src.bot.handlers.weather.dc"),
            patch("src.bot.handlers.weather.requests.get", side_effect=request_exception),
        ):
            await weather.handle(update, context)

        sent_message.edit_text.assert_called_once()
        assert "connecting to weather service" in sent_message.edit_text.call_args[0][0]

    @pytest.mark.anyio
    async def test_handle_key_error(self, mock_update):
        """Test weather handler when API response has missing data."""
        update, context = mock_update

        mock_bakchod = MagicMock()
        mock_bakchod.metadata = None

        sent_message = MagicMock()
        update.message.reply_text.return_value = sent_message

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "weather": [],
            "main": {},
            "wind": {},
            "name": "Test",
        }

        with (
            patch("src.bot.handlers.weather.WEATHER_API_KEY", "test_key"),
            patch(
                "src.bot.handlers.weather.bakchod_dao.get_bakchod_from_update",
                return_value=mock_bakchod,
            ),
            patch("src.bot.handlers.weather.dc"),
            patch("src.bot.handlers.weather.requests.get", return_value=mock_response),
        ):
            await weather.handle(update, context)

        sent_message.edit_text.assert_called_once()

    @pytest.mark.anyio
    async def test_handle_processing_exception(self, mock_update):
        """Test weather handler when processing exception occurs."""
        update, context = mock_update

        mock_bakchod = MagicMock()
        mock_bakchod.metadata = None

        sent_message = MagicMock()
        update.message.reply_text.return_value = sent_message

        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")

        with (
            patch("src.bot.handlers.weather.WEATHER_API_KEY", "test_key"),
            patch(
                "src.bot.handlers.weather.bakchod_dao.get_bakchod_from_update",
                return_value=mock_bakchod,
            ),
            patch("src.bot.handlers.weather.dc"),
            patch("src.bot.handlers.weather.requests.get", return_value=mock_response),
        ):
            await weather.handle(update, context)

        sent_message.edit_text.assert_called_once()

    @pytest.mark.anyio
    async def test_handle_outer_exception(self, mock_update):
        """Test weather handler when outer exception occurs."""
        update, context = mock_update

        with (
            patch(
                "src.bot.handlers.weather.bakchod_dao.get_bakchod_from_update",
                side_effect=Exception("Database error"),
            ),
            patch("src.bot.handlers.weather.dc") as mock_dc,
        ):
            await weather.handle(update, context)

        mock_dc.log_command_usage.assert_called_once()
        update.message.reply_text.assert_called_once()
        assert "Something went wrong" in update.message.reply_text.call_args[0][0]

    @patch("src.bot.handlers.weather.bakchod_dao")
    @patch("src.bot.handlers.weather.dc")
    @pytest.mark.anyio
    async def test_get_fallback_description_snow(self, mock_dc, mock_bakchod_dao):
        """Test _get_fallback_description with snow."""
        result = weather._get_fallback_description("heavy snow")

        assert "snow" in result.lower()

    @patch("src.bot.handlers.weather.bakchod_dao")
    @patch("src.bot.handlers.weather.dc")
    @pytest.mark.anyio
    async def test_get_fallback_description_fog(self, mock_dc, mock_bakchod_dao):
        """Test _get_fallback_description with fog."""
        result = weather._get_fallback_description("dense fog")

        assert "fog" in result.lower() or "mist" in result.lower()

    @patch("src.bot.handlers.weather.bakchod_dao")
    @patch("src.bot.handlers.weather.dc")
    @pytest.mark.anyio
    async def test_get_fallback_description_hot(self, mock_dc, mock_bakchod_dao):
        """Test _get_fallback_description with hot weather."""
        result = weather._get_fallback_description("extreme heat")

        assert "hot" in result.lower() or "heat" in result.lower()

    @patch("src.bot.handlers.weather.bakchod_dao")
    @patch("src.bot.handlers.weather.dc")
    @pytest.mark.anyio
    async def test_get_fallback_description_wind(self, mock_dc, mock_bakchod_dao):
        """Test _get_fallback_description with windy weather."""
        result = weather._get_fallback_description("strong breeze")

        assert "wind" in result.lower() or "breeze" in result.lower()

    @patch("src.bot.handlers.weather.bakchod_dao")
    @patch("src.bot.handlers.weather.dc")
    @pytest.mark.anyio
    async def test_generate_funny_description_llm_disabled(self, mock_dc, mock_bakchod_dao):
        """Test _generate_funny_description when LLM is disabled."""
        with patch("src.bot.handlers.weather.USE_LLM_FOR_DESCRIPTIONS", False):
            result = await weather._generate_funny_description("clear sky")

        assert isinstance(result, str)
        assert len(result) > 0

    @patch("src.bot.handlers.weather.bakchod_dao")
    @patch("src.bot.handlers.weather.dc")
    @pytest.mark.anyio
    async def test_generate_funny_description_llm_enabled(self, mock_dc, mock_bakchod_dao):
        """Test _generate_funny_description when LLM is enabled."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "It's brutally sunny outside."
        mock_client.chat.completions.create.return_value = mock_response

        with (
            patch("src.bot.handlers.weather.USE_LLM_FOR_DESCRIPTIONS", True),
            patch("src.bot.handlers.weather.openai_client", mock_client),
        ):
            result = await weather._generate_funny_description("clear sky")

        assert "sunny" in result.lower()

    @patch("src.bot.handlers.weather.bakchod_dao")
    @patch("src.bot.handlers.weather.dc")
    @pytest.mark.anyio
    async def test_generate_funny_description_llm_exception(self, mock_dc, mock_bakchod_dao):
        """Test _generate_funny_description when LLM raises exception."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API error")

        with (
            patch("src.bot.handlers.weather.USE_LLM_FOR_DESCRIPTIONS", True),
            patch("src.bot.handlers.weather.openai_client", mock_client),
        ):
            result = await weather._generate_funny_description("clear sky")

        assert isinstance(result, str)
        assert len(result) > 0

    @patch("src.bot.handlers.weather.bakchod_dao")
    @patch("src.bot.handlers.weather.dc")
    @pytest.mark.anyio
    async def test_generate_funny_description_no_client(self, mock_dc, mock_bakchod_dao):
        """Test _generate_funny_description when OpenAI client is None."""
        with (
            patch("src.bot.handlers.weather.USE_LLM_FOR_DESCRIPTIONS", True),
            patch("src.bot.handlers.weather.openai_client", None),
        ):
            result = await weather._generate_funny_description("clear sky")

        assert isinstance(result, str)
        assert len(result) > 0

    @patch("src.bot.handlers.weather.bakchod_dao")
    @patch("src.bot.handlers.weather.dc")
    @pytest.mark.anyio
    async def test_get_fallback_description_drizzle(self, mock_dc, mock_bakchod_dao):
        """Test _get_fallback_description with drizzle."""
        result = weather._get_fallback_description("light drizzle")

        assert isinstance(result, str)
        assert len(result) > 0

    @patch("src.bot.handlers.weather.bakchod_dao")
    @patch("src.bot.handlers.weather.dc")
    @pytest.mark.anyio
    async def test_get_fallback_description_shower(self, mock_dc, mock_bakchod_dao):
        """Test _get_fallback_description with shower."""
        result = weather._get_fallback_description("rain shower")

        assert isinstance(result, str)
        assert len(result) > 0
