from unittest.mock import MagicMock, patch

from src.db import message_dao


class TestMessageDao:
    @patch("src.db.message_dao.Bakchod")
    @patch("src.db.message_dao.Message")
    @patch("src.db.message_dao.metrics")
    def test_log_message_from_update_success(self, mock_metrics, mock_message, mock_bakchod):
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


class TestGetChatMessages:
    @staticmethod
    def _query(mock_message, rows):
        query = MagicMock()
        query.join.return_value = query
        query.where.return_value = query
        query.order_by.return_value.limit.return_value = rows
        mock_message.select.return_value = query
        mock_message.time_sent.__lt__ = MagicMock(return_value="time condition")
        return query

    @patch("src.db.message_dao.Message")
    def test_returns_messages_oldest_first(self, mock_message):
        query = self._query(mock_message, ["newest", "older", "oldest"])

        result = message_dao.get_chat_messages(123, limit=3)

        assert result == ["oldest", "older", "newest"]
        query.order_by.return_value.limit.assert_called_once_with(3)

    @patch("src.db.message_dao.Message")
    def test_filters_before_message_and_search(self, mock_message):
        query = self._query(mock_message, [])
        anchor = MagicMock()
        query.first.return_value = anchor

        message_dao.get_chat_messages(123, before_message_id=50, search="chai")

        mock_message.text.contains.assert_called_once_with("chai")
        mock_message.time_sent.__lt__.assert_called_once_with(anchor.time_sent)

    @patch("src.db.message_dao.Message")
    def test_unknown_before_message_is_ignored(self, mock_message):
        query = self._query(mock_message, ["m"])
        query.first.return_value = None

        assert message_dao.get_chat_messages(123, before_message_id=50) == ["m"]
        mock_message.time_sent.__lt__.assert_not_called()
