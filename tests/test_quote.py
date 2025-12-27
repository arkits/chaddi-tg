from unittest.mock import MagicMock, patch

from src.db import quote


class TestQuote:
    @patch("src.db.quote.bakchod_dao")
    @patch("src.db.quote.group_dao")
    @patch("src.db.quote.Quote")
    @patch("src.db.quote.metrics")
    @patch("src.db.quote.util")
    def test_add_quote_from_update_forwarded_message(
        self, mock_util, mock_metrics, mock_quote_class, mock_group_dao, mock_bakchod_dao
    ):
        """Test adding quote from forwarded message."""
        mock_forwarded_user = MagicMock()
        mock_forwarded_user.id = "original_author_id"
        mock_forwarded_user.username = "original_author"

        mock_quoted_message = MagicMock()
        mock_quoted_message.message_id = 123
        mock_quoted_message.text = "Test quote"
        mock_quoted_message.from_user = MagicMock()
        mock_quoted_message.from_user.id = "current_user_id"
        mock_quoted_message.forward_from = mock_forwarded_user
        mock_quoted_message.chat = MagicMock()
        mock_quoted_message.chat.id = "chat_id"

        mock_author_bakchod = MagicMock()
        mock_capture_bakchod = MagicMock()

        def get_or_create_bakchod_side_effect(user):
            if user.id == "original_author_id":
                return mock_author_bakchod
            return mock_capture_bakchod

        mock_bakchod_dao.get_or_create_bakchod_from_tg_user.side_effect = (
            get_or_create_bakchod_side_effect
        )

        mock_group = MagicMock()
        mock_group_dao.get_or_create_group_from_chat.return_value = mock_group

        mock_quote_instance = MagicMock()
        mock_quote_instance.message_id = 123
        mock_quote_class.create.return_value = mock_quote_instance

        mock_user = MagicMock()
        mock_user.id = "current_user_id"

        mock_update = MagicMock()
        mock_update.message = MagicMock()
        mock_update.message.reply_to_message = mock_quoted_message
        mock_update.message.from_user = mock_user
        mock_update.to_dict.return_value = {"test": "data"}

        result = quote.add_quote_from_update(mock_update)

        assert result == mock_quote_instance
        mock_quote_class.create.assert_called_once()
        mock_metrics.inc_message_count.assert_called_once()

    @patch("src.db.quote.bakchod_dao")
    @patch("src.db.quote.group_dao")
    @patch("src.db.quote.Quote")
    @patch("src.db.quote.metrics")
    def test_add_quote_from_update_non_forwarded(
        self, mock_metrics, mock_quote_class, mock_group_dao, mock_bakchod_dao
    ):
        """Test adding quote from non-forwarded message."""
        mock_quoted_message = MagicMock()
        mock_quoted_message.message_id = 123
        mock_quoted_message.text = "Test quote"
        mock_quoted_message.from_user = MagicMock()
        mock_quoted_message.from_user.id = "author_id"
        mock_quoted_message.forward_from = None
        mock_quoted_message.chat = MagicMock()
        mock_quoted_message.chat.id = "chat_id"

        mock_author_bakchod = MagicMock()
        mock_capture_bakchod = MagicMock()

        def get_or_create_bakchod_side_effect(user):
            if user.id == "author_id":
                return mock_author_bakchod
            return mock_capture_bakchod

        mock_bakchod_dao.get_or_create_bakchod_from_tg_user.side_effect = (
            get_or_create_bakchod_side_effect
        )

        mock_group = MagicMock()
        mock_group_dao.get_or_create_group_from_chat.return_value = mock_group

        mock_quote_instance = MagicMock()
        mock_quote_instance.message_id = 123
        mock_quote_class.create.return_value = mock_quote_instance

        mock_user = MagicMock()
        mock_user.id = "capture_user_id"

        mock_update = MagicMock()
        mock_update.message = MagicMock()
        mock_update.message.reply_to_message = mock_quoted_message
        mock_update.message.from_user = mock_user
        mock_update.to_dict.return_value = {"test": "data"}

        result = quote.add_quote_from_update(mock_update)

        assert result == mock_quote_instance

    @patch("src.db.quote.bakchod_dao")
    @patch("src.db.quote.group_dao")
    @patch("src.db.quote.Quote")
    def test_add_quote_from_update_fields(self, mock_quote_class, mock_group_dao, mock_bakchod_dao):
        """Test that quote fields are correctly set."""
        mock_quoted_message = MagicMock()
        mock_quoted_message.message_id = 123
        mock_quoted_message.text = "Test quote"
        mock_quoted_message.from_user = MagicMock()
        mock_quoted_message.from_user.id = "author_id"
        mock_quoted_message.forward_from = None
        mock_quoted_message.chat = MagicMock()
        mock_quoted_message.chat.id = "chat_id"

        mock_author_bakchod = MagicMock()
        mock_capture_bakchod = MagicMock()

        def get_or_create_bakchod_side_effect(user):
            if user.id == "author_id":
                return mock_author_bakchod
            return mock_capture_bakchod

        mock_bakchod_dao.get_or_create_bakchod_from_tg_user.side_effect = (
            get_or_create_bakchod_side_effect
        )

        mock_group = MagicMock()
        mock_group_dao.get_or_create_group_from_chat.return_value = mock_group

        mock_quote_instance = MagicMock()
        mock_quote_class.create.return_value = mock_quote_instance

        mock_user = MagicMock()
        mock_user.id = "capture_user_id"

        mock_update = MagicMock()
        mock_update.message = MagicMock()
        mock_update.message.reply_to_message = mock_quoted_message
        mock_update.message.from_user = mock_user
        mock_update.to_dict.return_value = {"test": "data"}

        quote.add_quote_from_update(mock_update)

        call_args = mock_quote_class.create.call_args
        assert call_args[1]["message_id"] == 123
        assert call_args[1]["text"] == "Test quote"
        assert call_args[1]["author_bakchod"] == mock_author_bakchod
        assert call_args[1]["quote_capture_bakchod"] == mock_capture_bakchod
        assert call_args[1]["quoted_in_group"] == mock_group
