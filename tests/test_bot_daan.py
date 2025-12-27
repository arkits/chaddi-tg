from unittest.mock import MagicMock, patch

import pytest
from telegram import Chat, Message, User

from src.bot.handlers import daan
from src.db import Bakchod


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
    message.entities = None
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
    message.entities = None

    update = MagicMock()
    update.message = message

    return update


class TestDaan:
    @patch("src.bot.handlers.daan.dc")
    @pytest.mark.anyio
    async def test_handle_no_parameters(self, mock_dc, mock_update):
        """Test daan handler with no parameters."""
        mock_update.message.text = "/daan"

        await daan.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_called_once_with("daan", mock_update)
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        if call_args[0]:
            assert "Syntax" in call_args[0][0]
        else:
            assert "Syntax" in call_args[1]["text"]

    @patch("src.bot.handlers.daan.dc")
    @patch("src.bot.handlers.daan.bakchod_dao.get_or_create_bakchod_from_tg_user")
    @pytest.mark.anyio
    async def test_handle_with_reply(self, mock_get_bakchod, mock_dc, mock_update_with_reply):
        """Test daan handler with reply to message."""
        mock_update_with_reply.message.text = "/daan 100"

        sender = MagicMock(spec=Bakchod)
        sender.rokda = 500

        receiver = MagicMock(spec=Bakchod)
        receiver.rokda = 200

        mock_get_bakchod.side_effect = [sender, receiver]

        await daan.handle(mock_update_with_reply, MagicMock())

        mock_dc.log_command_usage.assert_called_once_with("daan", mock_update_with_reply)
        assert mock_get_bakchod.call_count == 2
        sender.save.assert_called_once()
        receiver.save.assert_called_once()

    @patch("src.bot.handlers.daan.dc")
    @patch("src.bot.handlers.daan.bakchod_dao.get_or_create_bakchod_from_tg_user")
    @patch("src.bot.handlers.daan.bakchod_dao.get_bakchod_by_username")
    @pytest.mark.anyio
    async def test_handle_with_username_mention(
        self, mock_get_by_username, mock_get_or_create, mock_dc, mock_update
    ):
        """Test daan handler with username mention."""
        mock_update.message.text = "/daan @otheruser 100"

        sender = MagicMock(spec=Bakchod)
        sender.rokda = 500
        sender.tg_id = 123456

        receiver = MagicMock(spec=Bakchod)
        receiver.rokda = 200
        receiver.tg_id = 789012

        mock_get_or_create.return_value = sender
        mock_get_by_username.return_value = receiver

        await daan.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_called_once_with("daan", mock_update)
        mock_get_or_create.assert_called_once()
        mock_get_by_username.assert_called_once_with("otheruser")
        sender.save.assert_called_once()
        receiver.save.assert_called_once()

    @patch("src.bot.handlers.daan.dc")
    @patch("src.bot.handlers.daan.bakchod_dao.get_or_create_bakchod_from_tg_user")
    @pytest.mark.anyio
    async def test_handle_receiver_not_found(self, mock_get_bakchod, mock_dc, mock_update):
        """Test daan handler when receiver not found."""
        mock_update.message.text = "/daan @unknown 100"

        sender = MagicMock(spec=Bakchod)
        mock_get_bakchod.return_value = sender

        with patch(
            "src.bot.handlers.daan.bakchod_dao.get_bakchod_by_username"
        ) as mock_get_by_username:
            mock_get_by_username.return_value = None

            await daan.handle(mock_update, MagicMock())

            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "unknown" in call_args.lower()

    @patch("src.bot.handlers.daan.dc")
    @patch("src.bot.handlers.daan.bakchod_dao.get_or_create_bakchod_from_tg_user")
    @pytest.mark.anyio
    async def test_handle_invalid_daan_amount(self, mock_get_bakchod, mock_dc, mock_update):
        """Test daan handler with invalid amount."""
        mock_update.message.text = "/daan @otheruser abc"

        sender = MagicMock(spec=Bakchod)
        mock_get_bakchod.return_value = sender

        with patch(
            "src.bot.handlers.daan.bakchod_dao.get_bakchod_by_username"
        ) as mock_get_by_username:
            mock_get_by_username.return_value = MagicMock()

            await daan.handle(mock_update, MagicMock())

            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "₹okda" in call_args or "rokda" in call_args.lower()

    @patch("src.bot.handlers.daan.dc")
    @patch("src.bot.handlers.daan.bakchod_dao.get_or_create_bakchod_from_tg_user")
    @pytest.mark.anyio
    async def test_handle_insufficient_rokda(self, mock_get_bakchod, mock_dc, mock_update):
        """Test daan handler with insufficient rokda."""
        mock_update.message.text = "/daan @otheruser 1000"

        sender = MagicMock(spec=Bakchod)
        sender.rokda = 100
        sender.tg_id = 123456

        receiver = MagicMock(spec=Bakchod)
        receiver.rokda = 200
        receiver.tg_id = 789012

        mock_get_bakchod.side_effect = [sender, receiver]
        with patch(
            "src.bot.handlers.daan.bakchod_dao.get_bakchod_by_username"
        ) as mock_get_by_username:
            mock_get_by_username.return_value = receiver

            await daan.handle(mock_update, MagicMock())

            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "Gareeb" in call_args or "not enough" in call_args.lower()

    @patch("src.bot.handlers.daan.dc")
    @patch("src.bot.handlers.daan.bakchod_dao.get_or_create_bakchod_from_tg_user")
    @patch("src.bot.handlers.daan.bakchod_dao.get_bakchod_by_username")
    @pytest.mark.anyio
    async def test_handle_self_daan(
        self, mock_get_by_username, mock_get_bakchod, mock_dc, mock_update
    ):
        """Test daan handler when trying to donate to self."""
        mock_update.message.text = "/daan 100"

        sender = MagicMock(spec=Bakchod)
        sender.rokda = 500
        sender.tg_id = 123456

        mock_get_bakchod.return_value = sender
        mock_get_by_username.return_value = None

        await daan.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_called_once_with("daan", mock_update)
        # Since username lookup fails, it should reply with "Who dat??"
        call_args = mock_update.message.reply_text.call_args
        if call_args[0]:
            assert "dat" in call_args[0][0] or "be" in call_args[0][0]
        else:
            assert "dat" in call_args[1]["text"] or "be" in call_args[1]["text"]

    @patch("src.bot.handlers.daan.dc")
    @patch("src.bot.handlers.daan.bakchod_dao.get_or_create_bakchod_from_tg_user")
    @pytest.mark.anyio
    async def test_handle_infinite_daan(self, mock_get_bakchod, mock_dc, mock_update):
        """Test daan handler with infinite amount."""
        mock_update.message.text = "/daan @otheruser inf"

        sender = MagicMock(spec=Bakchod)
        sender.rokda = 500

        receiver = MagicMock(spec=Bakchod)
        receiver.rokda = 200

        mock_get_bakchod.side_effect = [sender, receiver]

        with patch(
            "src.bot.handlers.daan.bakchod_dao.get_bakchod_by_username"
        ) as mock_get_by_username:
            mock_get_by_username.return_value = receiver

            await daan.handle(mock_update, MagicMock())

            sender.save.assert_called_once()
            assert sender.rokda == 0

    @patch("src.bot.handlers.daan.dc")
    @patch("src.bot.handlers.daan.bakchod_dao.get_or_create_bakchod_from_tg_user")
    @pytest.mark.anyio
    async def test_handle_nan_daan(self, mock_get_bakchod, mock_dc, mock_update):
        """Test daan handler with NaN amount."""
        mock_update.message.text = "/daan @otheruser nan"

        sender = MagicMock(spec=Bakchod)
        sender.rokda = 500

        receiver = MagicMock(spec=Bakchod)
        receiver.rokda = 200

        mock_get_bakchod.side_effect = [sender, receiver]

        with patch(
            "src.bot.handlers.daan.bakchod_dao.get_bakchod_by_username"
        ) as mock_get_by_username:
            mock_get_by_username.return_value = receiver

            await daan.handle(mock_update, MagicMock())

            sender.save.assert_called_once()
            assert sender.rokda == 0

    @patch("src.bot.handlers.daan.dc")
    @patch("src.bot.handlers.daan.bakchod_dao.get_or_create_bakchod_from_tg_user")
    @pytest.mark.anyio
    async def test_handle_successful_daan(self, mock_get_bakchod, mock_dc, mock_update):
        """Test successful daan transaction."""
        mock_update.message.text = "/daan @otheruser 100"

        sender = MagicMock(spec=Bakchod)
        sender.rokda = 500
        sender.tg_id = 123456

        receiver = MagicMock(spec=Bakchod)
        receiver.rokda = 200
        receiver.tg_id = 789012

        mock_get_bakchod.return_value = sender

        with patch(
            "src.bot.handlers.daan.bakchod_dao.get_bakchod_by_username"
        ) as mock_get_by_username:
            mock_get_by_username.return_value = receiver
            with patch(
                "src.bot.handlers.daan.util.extract_pretty_name_from_bakchod"
            ) as mock_extract:
                # Need enough side_effects for the multiple calls
                mock_extract.side_effect = ["Test", "Other", "Test", "Other"]

                await daan.handle(mock_update, MagicMock())

                # Verify rokda was updated
                assert sender.rokda == 400
                assert receiver.rokda == 300
                sender.save.assert_called_once()
                receiver.save.assert_called_once()
                mock_update.message.reply_text.assert_called_once()
                call_args = mock_update.message.reply_text.call_args
                if call_args[0]:
                    assert "daan" in call_args[0][0]
                    assert "100" in call_args[0][0]
                else:
                    assert "daan" in call_args[1]["text"]
                    assert "100" in call_args[1]["text"]
