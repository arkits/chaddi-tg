from unittest.mock import MagicMock, patch

import pytest
from telegram import Chat, Message, User

from src.bot.handlers import chutiya


@pytest.fixture
def mock_update():
    """Create a mock Telegram Update object for testing."""
    user = MagicMock(spec=User)
    user.id = 123456
    user.username = "testuser"
    user.first_name = "Test"

    reply_user = MagicMock(spec=User)
    reply_user.id = 789012
    reply_user.username = "replyuser"
    reply_user.first_name = "Reply"

    chat = MagicMock(spec=Chat)
    chat.id = -1001234567890
    chat.type = "group"

    message = MagicMock(spec=Message)
    message.message_id = 1
    message.from_user = user
    message.chat = chat
    message.text = "/chutiya"
    message.reply_to_message = None

    reply_message = MagicMock(spec=Message)
    reply_message.from_user = reply_user

    update = MagicMock()
    update.message = message
    update.message.reply_to_message = reply_message

    return update


class TestChutiya:
    @patch("src.bot.handlers.chutiya.random")
    @patch("src.bot.handlers.chutiya.dc")
    @patch("src.bot.handlers.chutiya.util")
    @pytest.mark.anyio
    async def test_handle_without_reply(self, mock_util, mock_dc, mock_random, mock_update):
        """Test chutiya handler without reply."""
        mock_update.message.reply_to_message = None
        mock_util.extract_pretty_name_from_tg_user.return_value = "Test User"
        mock_dc.log_command_usage = MagicMock()
        mock_util.get_verb_past_lookup.return_value = {
            0: {
                "word1": "cool",
                "word2": "huge",
                "word3": "ugly",
                "word4": "terrible",
                "word5": "yucky",
                "word6": "awesome",
                "word7": "idiot",
            }
        }
        mock_random.choice.side_effect = [
            "Cool",
            "Huge",
            "Ugly",
            "Terrible",
            "Yucky",
            "Awesome",
            "Idiot",
        ]

        await chutiya.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_called_once_with("chutiya", mock_update)
        mock_util.extract_pretty_name_from_tg_user.assert_called_once_with(
            mock_update.message.from_user
        )
        mock_update.message.reply_text.assert_called_once()

    @patch("src.bot.handlers.chutiya.random")
    @patch("src.bot.handlers.chutiya.dc")
    @patch("src.bot.handlers.chutiya.util")
    @pytest.mark.anyio
    async def test_handle_with_reply(self, mock_util, mock_dc, mock_random, mock_update):
        """Test chutiya handler with reply."""
        mock_util.extract_pretty_name_from_tg_user.return_value = "Reply User"
        mock_dc.log_command_usage = MagicMock()
        mock_util.get_verb_past_lookup.return_value = {
            0: {
                "word1": "cool",
                "word2": "huge",
                "word3": "ugly",
                "word4": "terrible",
                "word5": "yucky",
                "word6": "awesome",
                "word7": "idiot",
            }
        }
        mock_random.choice.side_effect = [
            "Cool",
            "Huge",
            "Ugly",
            "Terrible",
            "Yucky",
            "Awesome",
            "Idiot",
        ]

        await chutiya.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_called_once_with("chutiya", mock_update)
        mock_util.extract_pretty_name_from_tg_user.assert_called_once_with(
            mock_update.message.reply_to_message.from_user
        )
        mock_update.message.reply_to_message.reply_text.assert_called_once()

    @patch("src.bot.handlers.chutiya.random")
    @patch("src.bot.handlers.chutiya.dc")
    @patch("src.bot.handlers.chutiya.util")
    @pytest.mark.anyio
    async def test_handle_insulting_bot(self, mock_util, mock_dc, mock_random, mock_update):
        """Test chutiya handler when trying to insult the bot itself."""
        mock_util.extract_pretty_name_from_tg_user.return_value = "chaddi_bot"
        mock_dc.log_command_usage = MagicMock()

        await chutiya.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_called_once_with("chutiya", mock_update)
        mock_update.message.reply_sticker.assert_called_once_with(
            sticker="CAADAQADrAEAAp6M4Ahtgp9JaiLJPxYE"
        )

    @patch("src.bot.handlers.chutiya.dc")
    @pytest.mark.anyio
    async def test_handle_with_exception(self, mock_dc, mock_update):
        """Test chutiya handler when an exception occurs."""
        with patch("src.bot.handlers.chutiya.util") as mock_util:
            mock_util.extract_pretty_name_from_tg_user.side_effect = Exception("Error")

            await chutiya.handle(mock_update, MagicMock())

            mock_dc.log_command_usage.assert_called_once_with("chutiya", mock_update)

    @patch("src.bot.handlers.chutiya.random")
    @patch("src.bot.handlers.chutiya.util")
    def test_acronymify(self, mock_util, mock_random):
        """Test acronymify function."""
        mock_util.get_verb_past_lookup.return_value = {
            0: {
                "word1": "apple",
                "word2": "banana",
                "word3": "cherry",
            }
        }
        mock_random.choice.side_effect = ["Test", "Eat", "Sleep", "Test"]

        result = chutiya.acronymify("test")

        assert "\n T = `Test`" in result
        assert "\n E = `Eat`" in result
        assert "\n S = `Sleep`" in result
        assert "\n T = `Test`" in result

    @patch("src.bot.handlers.chutiya.util")
    def test_pick_a_word(self, mock_util):
        """Test pick_a_word function."""
        mock_util.get_verb_past_lookup.return_value = {
            0: {
                "word1": "apple",
                "word2": "banana",
                "word3": "cherry",
            }
        }

        result = chutiya.pick_a_word("a")

        assert result in ["apple"]
        mock_util.get_verb_past_lookup.assert_called_once()

    @patch("src.bot.handlers.chutiya.util")
    def test_pick_a_word_no_match(self, mock_util):
        """Test pick_a_word when no words start with the letter."""
        mock_util.get_verb_past_lookup.return_value = {
            0: {
                "word1": "apple",
                "word2": "banana",
            }
        }

        with pytest.raises(IndexError):
            chutiya.pick_a_word("z")
