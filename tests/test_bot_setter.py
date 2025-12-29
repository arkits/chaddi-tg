from unittest.mock import MagicMock, patch

import pytest
from telegram import Chat, Message, User

from src.bot.handlers import setter
from src.db import Bakchod, Group


@pytest.fixture
def mock_update():
    """Create a mock Telegram Update object for testing."""
    user = MagicMock(spec=User)
    user.id = 123456
    user.username = "testuser"
    user.first_name = "Test"

    other_user = MagicMock(spec=User)
    other_user.id = 789012
    other_user.username = "otheruser"
    other_user.first_name = "Other"

    chat = MagicMock(spec=Chat)
    chat.id = -1001234567890
    chat.type = "group"

    message = MagicMock(spec=Message)
    message.message_id = 1
    message.from_user = user
    message.chat = chat
    message.reply_to_message = None

    update = MagicMock()
    update.message = message

    return update


@pytest.fixture
def mock_update_with_reply():
    """Create a mock Telegram Update object with reply."""
    user = MagicMock(spec=User)
    user.id = 123456
    user.username = "testuser"
    user.first_name = "Test"

    other_user = MagicMock(spec=User)
    other_user.id = 789012
    other_user.username = "otheruser"
    other_user.first_name = "Other"

    chat = MagicMock(spec=Chat)
    chat.id = -1001234567890
    chat.type = "group"

    reply_message = MagicMock(spec=Message)
    reply_message.from_user = other_user

    message = MagicMock(spec=Message)
    message.message_id = 1
    message.from_user = user
    message.chat = chat
    message.reply_to_message = reply_message

    update = MagicMock()
    update.message = message

    return update


class TestSetter:
    @patch("src.bot.handlers.setter.dc")
    @pytest.mark.anyio
    async def test_handle_no_parameters(self, mock_dc, mock_update):
        """Test setter handler with no parameters."""
        mock_update.message.text = "/set"

        await setter.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_called_once_with("set", mock_update)
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        if call_args[0]:
            assert "what you want to set" in call_args[0][0].lower()
        else:
            assert call_args[1]["text"].lower()

    @patch("src.bot.handlers.setter.dc")
    @patch("src.bot.handlers.setter.util.is_admin_tg_user", return_value=True)
    @patch("src.bot.handlers.setter.Bakchod.get_by_id")
    @pytest.mark.anyio
    async def test_handle_set_rokda_admin(
        self, mock_get_bakchod, mock_is_admin, mock_dc, mock_update
    ):
        """Test setter handler setting rokda with admin."""
        mock_update.message.text = "/set rokda 1337"
        mock_bakchod = MagicMock(spec=Bakchod)
        mock_bakchod.rokda = 1337
        mock_get_bakchod.return_value = mock_bakchod

        await setter.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_called_once_with("set", mock_update)
        mock_bakchod.save.assert_called_once()

    @patch("src.bot.handlers.setter.dc")
    @patch("src.bot.handlers.setter.util.is_admin_tg_user", return_value=False)
    @pytest.mark.anyio
    async def test_handle_set_rokda_non_admin(self, mock_is_admin, mock_dc, mock_update):
        """Test setter handler setting rokda with non-admin."""
        mock_update.message.text = "/set rokda 1337"

        await setter.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_called_once_with("set", mock_update)
        call_args = mock_update.message.reply_text.call_args
        if call_args[0]:
            assert "Not allowed" in call_args[0][0]
        else:
            assert "Not allowed" in call_args[1]["text"]

    @patch("src.bot.handlers.setter.dc")
    @patch("src.bot.handlers.setter.util.is_admin_tg_user", return_value=True)
    @pytest.mark.anyio
    async def test_handle_set_rokda_with_reply(
        self, mock_is_admin, mock_dc, mock_update_with_reply
    ):
        """Test setter handler setting rokda with reply."""
        mock_update_with_reply.message.text = "/set rokda 1337"
        with patch("src.bot.handlers.setter.Bakchod.get_by_id") as mock_get_bakchod:
            mock_bakchod = MagicMock(spec=Bakchod)
            mock_bakchod.rokda = 1337
            mock_get_bakchod.return_value = mock_bakchod

            await setter.handle(mock_update_with_reply, MagicMock())

            mock_get_bakchod.assert_called_once_with(789012)

    @patch("src.bot.handlers.setter.dc")
    @patch("src.bot.handlers.setter.util.is_admin_tg_user", return_value=True)
    @patch("src.bot.handlers.setter.group_dao.get_group_from_update")
    @pytest.mark.anyio
    async def test_handle_set_gm_on(self, mock_get_group, mock_is_admin, mock_dc, mock_update):
        """Test setter handler enabling good morning."""
        mock_update.message.text = "/set gm on"
        mock_group = MagicMock(spec=Group)
        mock_group.metadata = {}
        mock_get_group.return_value = mock_group

        await setter.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_called_once_with("set", mock_update)
        assert mock_group.metadata["good_morning_enabled"] is True
        mock_group.save.assert_called_once()

    @patch("src.bot.handlers.setter.dc")
    @patch("src.bot.handlers.setter.util.is_admin_tg_user", return_value=True)
    @patch("src.bot.handlers.setter.group_dao.get_group_from_update")
    @pytest.mark.anyio
    async def test_handle_set_gm_off(self, mock_get_group, mock_is_admin, mock_dc, mock_update):
        """Test setter handler disabling good morning."""
        mock_update.message.text = "/set gm off"
        mock_group = MagicMock(spec=Group)
        mock_group.metadata = {}
        mock_get_group.return_value = mock_group

        await setter.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_called_once_with("set", mock_update)
        assert mock_group.metadata["good_morning_enabled"] is False
        mock_group.save.assert_called_once()

    @patch("src.bot.handlers.setter.dc")
    @patch("src.bot.handlers.setter.util.is_admin_tg_user", return_value=False)
    @pytest.mark.anyio
    async def test_handle_set_gm_non_admin(self, mock_is_admin, mock_dc, mock_update):
        """Test setter handler setting gm with non-admin."""
        mock_update.message.text = "/set gm on"

        await setter.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_called_once_with("set", mock_update)
        call_args = mock_update.message.reply_text.call_args
        if call_args[0]:
            assert "Only admins" in call_args[0][0]
        else:
            assert "Only admins" in call_args[1]["text"]

    @patch("src.bot.handlers.setter.dc")
    @patch("src.bot.handlers.setter.util.is_admin_tg_user", return_value=True)
    @patch("src.bot.handlers.setter.group_dao.get_group_from_update")
    @pytest.mark.anyio
    async def test_handle_set_ask_on(self, mock_get_group, mock_is_admin, mock_dc, mock_update):
        """Test setter handler enabling ask command."""
        mock_update.message.text = "/set ask on"
        mock_group = MagicMock(spec=Group)
        mock_group.metadata = {}
        mock_get_group.return_value = mock_group

        await setter.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_called_once_with("set", mock_update)
        assert "ask" in mock_group.metadata["enabled_commands"]
        mock_group.save.assert_called_once()

    @patch("src.bot.handlers.setter.dc")
    @patch("src.bot.handlers.setter.util.is_admin_tg_user", return_value=True)
    @patch("src.bot.handlers.setter.group_dao.get_group_from_update")
    @pytest.mark.anyio
    async def test_handle_set_ask_off(self, mock_get_group, mock_is_admin, mock_dc, mock_update):
        """Test setter handler disabling ask command."""
        mock_update.message.text = "/set ask off"
        mock_group = MagicMock(spec=Group)
        mock_group.metadata = {"enabled_commands": ["ask"]}
        mock_get_group.return_value = mock_group

        await setter.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_called_once_with("set", mock_update)
        assert "ask" not in mock_group.metadata["enabled_commands"]
        mock_group.save.assert_called_once()

    @patch("src.bot.handlers.setter.dc")
    @patch("src.bot.handlers.setter.util.is_admin_tg_user", return_value=True)
    @patch("src.bot.handlers.setter.group_dao.get_group_from_update")
    @pytest.mark.anyio
    async def test_handle_set_ai_clear(self, mock_get_group, mock_is_admin, mock_dc, mock_update):
        """Test setter handler clearing AI conversation thread."""
        mock_update.message.text = "/set ai clear"
        mock_group = MagicMock(spec=Group)
        mock_group.metadata = {}
        mock_get_group.return_value = mock_group

        await setter.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_called_once_with("set", mock_update)
        assert "ai_thread_cleared_at" in mock_group.metadata
        mock_group.save.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        if call_args[0]:
            assert "cleared" in call_args[0][0]
        else:
            assert "cleared" in call_args[1]["text"]

    @patch("src.bot.handlers.setter.dc")
    @patch("src.bot.handlers.setter.util.is_admin_tg_user", return_value=True)
    @patch("src.bot.handlers.setter.group_dao.get_group_from_update")
    @pytest.mark.anyio
    async def test_handle_set_ai_clear_non_admin(
        self, mock_get_group, mock_is_admin, mock_dc, mock_update
    ):
        """Test setter handler clearing AI thread by non-admin."""
        mock_is_admin.return_value = False
        mock_update.message.text = "/set ai clear"

        await setter.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_called_once_with("set", mock_update)
        mock_get_group.assert_not_called()
        call_args = mock_update.message.reply_text.call_args
        if call_args[0]:
            assert "Only admins" in call_args[0][0]
        else:
            assert "Only admins" in call_args[1]["text"]

    @patch("src.bot.handlers.setter.dc")
    @pytest.mark.anyio
    async def test_handle_unknown_set_type(self, mock_dc, mock_update):
        """Test setter handler with unknown set type."""
        mock_update.message.text = "/set unknown value"

        await setter.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_called_once_with("set", mock_update)
        call_args = mock_update.message.reply_text.call_args
        if call_args[0]:
            assert "Can't set that" in call_args[0][0]
        else:
            assert "Can't set that" in call_args[1]["text"]

    @patch("src.bot.handlers.setter.util.is_admin_tg_user")
    def test_parse_request_no_set_type(self, mock_is_admin, mock_update):
        """Test parse_request with no set type."""
        request = ["/set"]

        result = setter.parse_request(
            request, mock_update.message.from_user, mock_update.message.from_user, mock_update
        )

        assert "what you want to set" in result.lower()

    @patch("src.bot.handlers.setter.util.is_admin_tg_user")
    def test_set_bakchod_rokda(self, mock_is_admin):
        """Test set_bakchod_rokda function."""
        mock_user = MagicMock()
        mock_user.id = 123456
        mock_bakchod = MagicMock(spec=Bakchod)
        mock_bakchod.rokda = 1337

        with patch("src.bot.handlers.setter.Bakchod.get_by_id") as mock_get:
            mock_get.return_value = mock_bakchod
            result = setter.set_bakchod_rokda(1337, mock_user)

            assert "1337" in result
            mock_bakchod.save.assert_called_once()
