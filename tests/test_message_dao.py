from unittest.mock import MagicMock, patch

from src.db import message_dao


class TestMessageDao:
    @patch("src.db.message_dao.Bakchod")
    @patch("src.db.message_dao.Message")
    @patch("src.db.message_dao.metrics")
    @patch("src.db.message_dao.util")
    def test_log_message_from_update_success(
        self, mock_util, mock_metrics, mock_message, mock_bakchod
    ):
        """Test successfully logging a message from update."""
        mock_bakchod_instance = MagicMock()
        mock_bakchod.get_by_id.return_value = mock_bakchod_instance

        mock_message_instance = MagicMock()
        mock_message_instance.message_id = 123
        mock_message.create.return_value = mock_message_instance

        mock_user = MagicMock()
        mock_user.id = "user_id"

        mock_chat = MagicMock()
        mock_chat.id = "chat_id"

        mock_message_update = MagicMock()
        mock_message_update.message_id = 123
        mock_message_update.text = "Test message"
        mock_message_update.from_user = mock_user
        mock_message_update.chat = mock_chat
        mock_message_update.to_dict.return_value = {"test": "data"}

        mock_update = MagicMock()
        mock_update.message = mock_message_update

        result = message_dao.log_message_from_update(mock_update)

        assert result == mock_message_instance
        mock_bakchod.get_by_id.assert_called_once_with("user_id")
        mock_message.create.assert_called_once()
        mock_metrics.inc_message_count.assert_called_once()

    @patch("src.db.message_dao.Bakchod")
    @patch("src.db.message_dao.Message")
    def test_log_message_from_update_fields(self, mock_message, mock_bakchod):
        """Test that message fields are correctly set."""
        mock_bakchod_instance = MagicMock()
        mock_bakchod_instance.username = "testuser"
        mock_bakchod.get_by_id.return_value = mock_bakchod_instance

        mock_message_instance = MagicMock()
        mock_message.create.return_value = mock_message_instance

        mock_user = MagicMock()
        mock_user.id = "user_id"

        mock_chat = MagicMock()
        mock_chat.id = "chat_id"

        mock_message_update = MagicMock()
        mock_message_update.message_id = 123
        mock_message_update.text = "Test message"
        mock_message_update.from_user = mock_user
        mock_message_update.chat = mock_chat
        mock_message_update.to_dict.return_value = {"test": "data"}

        mock_update = MagicMock()
        mock_update.message = mock_message_update

        message_dao.log_message_from_update(mock_update)

        call_args = mock_message.create.call_args
        assert call_args[1]["message_id"] == 123
        assert call_args[1]["text"] == "Test message"
        assert call_args[1]["from_bakchod"] == mock_bakchod_instance
        assert call_args[1]["to_id"] == "chat_id"
