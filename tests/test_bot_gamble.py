from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from telegram import Chat, Message, Update, User

from src.bot.handlers import gamble
from src.db import Bakchod


@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.from_user = MagicMock(spec=User)
    update.message.from_user.id = 123
    update.message.chat = MagicMock(spec=Chat)
    update.message.chat.id = 456
    return update


@pytest.fixture
def mock_bakchod():
    bakchod = MagicMock(spec=Bakchod)
    bakchod.tg_id = "123"
    bakchod.rokda = 1000
    bakchod.metadata = {}
    bakchod.save = MagicMock()
    return bakchod


class TestCanBakchodGamble:
    def test_can_gamble_first_time(self, mock_bakchod):
        mock_bakchod.metadata = {}
        can_gamble, response = gamble.can_bakchod_gamble(mock_bakchod)
        assert can_gamble is True
        assert response is None

    def test_can_gamble_sufficient_rokda(self, mock_bakchod):
        mock_bakchod.metadata = {
            "last_time_gambled": (datetime.now() - timedelta(minutes=2)).isoformat()
        }
        mock_bakchod.rokda = 100
        can_gamble, response = gamble.can_bakchod_gamble(mock_bakchod)
        assert can_gamble is True
        assert response is None

    def test_can_gamble_insufficient_rokda(self, mock_bakchod):
        mock_bakchod.metadata = {
            "last_time_gambled": (datetime.now() - timedelta(minutes=2)).isoformat()
        }
        mock_bakchod.rokda = 10
        can_gamble, response = gamble.can_bakchod_gamble(mock_bakchod)
        assert can_gamble is False
        assert response is not None
        assert "50" in response

    def test_can_gamble_too_soon(self, mock_bakchod):
        mock_bakchod.metadata = {
            "last_time_gambled": (datetime.now() - timedelta(seconds=30)).isoformat()
        }
        mock_bakchod.rokda = 100
        can_gamble, response = gamble.can_bakchod_gamble(mock_bakchod)
        assert can_gamble is False
        assert response is not None
        assert "addiction" in response


class TestGamble:
    @patch("src.bot.handlers.gamble.util.get_random_bakchod_from_group")
    @patch("src.bot.handlers.gamble.random.random")
    def test_gamble_win_500(self, mock_random, mock_get_bakchod, mock_bakchod, mock_update):
        mock_random.return_value = 0.99
        mock_get_bakchod.return_value = None

        result = gamble.gamble(mock_bakchod, mock_update)

        assert result is not None
        assert "500" in result
        assert mock_bakchod.rokda >= 1500

    @patch("src.bot.handlers.gamble.util.get_random_bakchod_from_group")
    @patch("src.bot.handlers.gamble.random.random")
    def test_gamble_win_400(self, mock_random, mock_get_bakchod, mock_bakchod, mock_update):
        mock_random.return_value = 0.96
        mock_get_bakchod.return_value = None

        result = gamble.gamble(mock_bakchod, mock_update)

        assert result is not None
        assert "400" in result
        assert mock_bakchod.rokda >= 1400

    @patch("src.bot.handlers.gamble.util.get_random_bakchod_from_group")
    @patch("src.bot.handlers.gamble.random.random")
    def test_gamble_win_300(self, mock_random, mock_get_bakchod, mock_bakchod, mock_update):
        mock_random.return_value = 0.92
        mock_get_bakchod.return_value = None

        result = gamble.gamble(mock_bakchod, mock_update)

        assert result is not None
        assert "300" in result
        assert mock_bakchod.rokda >= 1300

    @patch("src.bot.handlers.gamble.util.get_random_bakchod_from_group")
    @patch("src.bot.handlers.gamble.random.random")
    def test_gamble_win_200_with_gift(
        self, mock_random, mock_get_bakchod, mock_bakchod, mock_update
    ):
        mock_random.return_value = 0.88
        random_bakchod = MagicMock()
        random_bakchod.rokda = 500
        random_bakchod.pretty_name = "TestUser"
        mock_get_bakchod.return_value = random_bakchod

        result = gamble.gamble(mock_bakchod, mock_update)

        assert result is not None
        assert "200" in result
        assert mock_bakchod.rokda >= 1200
        assert random_bakchod.rokda == 515

    @patch("src.bot.handlers.gamble.util.get_random_bakchod_from_group")
    @patch("src.bot.handlers.gamble.random.random")
    def test_gamble_win_100(self, mock_random, mock_get_bakchod, mock_bakchod, mock_update):
        mock_random.return_value = 0.80
        mock_get_bakchod.return_value = None

        result = gamble.gamble(mock_bakchod, mock_update)

        assert result is not None
        assert "100" in result
        assert mock_bakchod.rokda >= 1100

    @patch("src.bot.handlers.gamble.util.get_random_bakchod_from_group")
    @patch("src.bot.handlers.gamble.random.random")
    def test_gamble_win_1_pity(self, mock_random, mock_get_bakchod, mock_bakchod, mock_update):
        mock_random.return_value = 0.60
        mock_get_bakchod.return_value = None

        result = gamble.gamble(mock_bakchod, mock_update)

        assert result is not None
        assert "1" in result
        assert mock_bakchod.rokda >= 1001

    @patch("src.bot.handlers.gamble.util.get_random_bakchod_from_group")
    @patch("src.bot.handlers.gamble.random.random")
    def test_gamble_lose_100(self, mock_random, mock_get_bakchod, mock_bakchod, mock_update):
        mock_random.return_value = 0.50
        random_bakchod = MagicMock()
        random_bakchod.rokda = 500
        random_bakchod.pretty_name = "TestUser"
        mock_get_bakchod.return_value = random_bakchod

        result = gamble.gamble(mock_bakchod, mock_update)

        assert result is not None
        assert mock_bakchod.rokda == 900
        assert random_bakchod.rokda == 600

    @patch("src.bot.handlers.gamble.util.get_random_bakchod_from_group")
    @patch("src.bot.handlers.gamble.random.random")
    def test_gamble_lose_250(self, mock_random, mock_get_bakchod, mock_bakchod, mock_update):
        mock_random.return_value = 0.40
        mock_get_bakchod.return_value = None

        result = gamble.gamble(mock_bakchod, mock_update)

        assert result is not None
        assert "250" in result
        assert mock_bakchod.rokda == 750

    @patch("src.bot.handlers.gamble.util.get_random_bakchod_from_group")
    @patch("src.bot.handlers.gamble.random.random")
    def test_gamble_lose_375(self, mock_random, mock_get_bakchod, mock_bakchod, mock_update):
        mock_random.return_value = 0.30
        mock_get_bakchod.return_value = None

        result = gamble.gamble(mock_bakchod, mock_update)

        assert result is not None
        assert "375" in result
        assert mock_bakchod.rokda == 625

    @patch("src.bot.handlers.gamble.util.get_random_bakchod_from_group")
    @patch("src.bot.handlers.gamble.random.random")
    def test_gamble_lose_500_mugged(self, mock_random, mock_get_bakchod, mock_bakchod, mock_update):
        mock_random.return_value = 0.20
        random_bakchod = MagicMock()
        random_bakchod.rokda = 500
        random_bakchod.pretty_name = "TestUser"
        mock_get_bakchod.return_value = random_bakchod

        result = gamble.gamble(mock_bakchod, mock_update)

        assert result is not None
        assert "500" in result
        assert mock_bakchod.rokda == 500
        assert random_bakchod.rokda == 1000

    @patch("src.bot.handlers.gamble.util.get_random_bakchod_from_group")
    @patch("src.bot.handlers.gamble.random.random")
    def test_gamble_lose_1000_raid(self, mock_random, mock_get_bakchod, mock_bakchod, mock_update):
        mock_random.return_value = 0.10
        mock_get_bakchod.return_value = None

        result = gamble.gamble(mock_bakchod, mock_update)

        assert result is not None
        assert "1000" in result
        assert mock_bakchod.rokda == 0

    @patch("src.bot.handlers.gamble.util.get_random_bakchod_from_group")
    @patch("src.bot.handlers.gamble.random.random")
    def test_gamble_lose_everything(self, mock_random, mock_get_bakchod, mock_bakchod, mock_update):
        mock_random.return_value = 0.005
        random_bakchod = MagicMock()
        random_bakchod.rokda = 0
        random_bakchod.pretty_name = "TestUser"
        mock_get_bakchod.return_value = random_bakchod

        result = gamble.gamble(mock_bakchod, mock_update)

        assert result is not None
        assert "fortune" in result
        assert mock_bakchod.rokda == 1
        assert random_bakchod.rokda == 1000

    @patch("src.bot.handlers.gamble.util.get_random_bakchod_from_group")
    @patch("src.bot.handlers.gamble.random.random")
    def test_gamble_bankruptcy_protection(
        self, mock_random, mock_get_bakchod, mock_bakchod, mock_update
    ):
        mock_random.return_value = 0.10
        mock_bakchod.rokda = 800
        mock_get_bakchod.return_value = None

        result = gamble.gamble(mock_bakchod, mock_update)

        assert result is not None
        assert "bankrupt" in result
        assert mock_bakchod.rokda == 0

    @patch("src.bot.handlers.gamble.util.get_random_bakchod_from_group")
    @patch("src.bot.handlers.gamble.random.random")
    def test_gamble_solo_no_group_members(
        self, mock_random, mock_get_bakchod, mock_bakchod, mock_update
    ):
        mock_random.return_value = 0.50
        mock_get_bakchod.return_value = None

        result = gamble.gamble(mock_bakchod, mock_update)

        assert result is not None

    @patch("src.bot.handlers.gamble.util.get_random_bakchod_from_group")
    @patch("src.bot.handlers.gamble.random.random")
    def test_gamble_with_username(self, mock_random, mock_get_bakchod, mock_bakchod, mock_update):
        mock_random.return_value = 0.50
        random_bakchod = MagicMock()
        random_bakchod.rokda = 500
        random_bakchod.pretty_name = None
        random_bakchod.username = "testuser"
        mock_get_bakchod.return_value = random_bakchod

        result = gamble.gamble(mock_bakchod, mock_update)

        assert result is not None
        assert "testuser" in result

    @patch("src.bot.handlers.gamble.util.get_random_bakchod_from_group")
    @patch("src.bot.handlers.gamble.random.random")
    def test_gamble_saves_metadata(self, mock_random, mock_get_bakchod, mock_bakchod, mock_update):
        mock_random.return_value = 0.60
        mock_get_bakchod.return_value = None

        gamble.gamble(mock_bakchod, mock_update)

        assert "last_time_gambled" in mock_bakchod.metadata
        mock_bakchod.save.assert_called_once()


class TestHandle:
    @pytest.mark.anyio
    async def test_handle_success(self, mock_update, mock_bakchod):
        mock_update.message.reply_text = MagicMock()

        with (
            patch("src.bot.handlers.gamble.dc"),
            patch("src.bot.handlers.gamble.bakchod_dao") as mock_bakchod_dao,
            patch("src.bot.handlers.gamble.util") as mock_util,
        ):
            mock_bakchod_dao.get_or_create_bakchod_from_tg_user.return_value = mock_bakchod
            mock_util.get_random_bakchod_from_group.return_value = None

            await gamble.handle(mock_update, MagicMock())

            mock_update.message.reply_text.assert_called_once()

    @pytest.mark.anyio
    async def test_handle_cannot_gamble(self, mock_update, mock_bakchod):
        with (
            patch("src.bot.handlers.gamble.dc"),
            patch("src.bot.handlers.gamble.bakchod_dao") as mock_bakchod_dao,
        ):
            mock_bakchod_dao.get_or_create_bakchod_from_tg_user.return_value = mock_bakchod
            mock_bakchod.metadata = {"last_time_gambled": datetime.now().isoformat()}

            await gamble.handle(mock_update, MagicMock())

            mock_update.message.reply_text.assert_called_once()
            args = mock_update.message.reply_text.call_args[0][0]
            assert "addiction" in args

    @pytest.mark.anyio
    async def test_handle_exception(self, mock_update):
        with (
            patch("src.bot.handlers.gamble.dc"),
            patch("src.bot.handlers.gamble.bakchod_dao") as mock_bakchod_dao,
        ):
            mock_bakchod_dao.get_or_create_bakchod_from_tg_user.side_effect = Exception("Error")

            await gamble.handle(mock_update, MagicMock())
