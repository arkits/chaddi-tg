from unittest.mock import MagicMock, patch

from peewee import DoesNotExist

from src.db import group_dao


class TestGroupDao:
    @patch("src.db.group_dao.Group")
    def test_get_or_create_group_from_chat_existing(self, mock_group):
        """Test retrieving existing group"""
        mock_group_instance = MagicMock()
        mock_group.get.return_value = mock_group_instance

        mock_chat = MagicMock()
        mock_chat.id = "test_group_id"

        result = group_dao.get_or_create_group_from_chat(mock_chat)

        assert result == mock_group_instance
        mock_group.get.assert_called_once()
        mock_group.create.assert_not_called()

    @patch("src.db.group_dao.Group")
    def test_get_or_create_group_from_chat_new(self, mock_group):
        """Test creating new group"""
        mock_group.get.side_effect = DoesNotExist()
        mock_group_instance = MagicMock()
        mock_group.create.return_value = mock_group_instance

        mock_chat = MagicMock()
        mock_chat.id = "new_group_id"
        mock_chat.title = "New Group"

        result = group_dao.get_or_create_group_from_chat(mock_chat)

        assert result == mock_group_instance
        mock_group.create.assert_called_once()

    @patch("src.db.group_dao.Group")
    def test_get_group_by_id_success(self, mock_group):
        """Test successful group retrieval by id"""
        mock_group_instance = MagicMock()
        mock_group.get.return_value = mock_group_instance

        result = group_dao.get_group_by_id("test_group_id")

        assert result == mock_group_instance
        mock_group.get.assert_called_once()

    @patch("src.db.group_dao.Group")
    def test_get_group_by_id_not_exists(self, mock_group):
        """Test when group doesn't exist"""
        mock_group.get.side_effect = DoesNotExist()

        result = group_dao.get_group_by_id("nonexistent_group")

        assert result is None

    @patch("src.db.group_dao.GroupMember")
    @patch("src.db.group_dao.Group")
    def test_get_all_groupmembers_by_group_id(self, mock_group, mock_groupmember):
        """Test retrieving all group members"""
        mock_member1 = MagicMock()
        mock_member2 = MagicMock()
        mock_members = [mock_member1, mock_member2]

        mock_groupmember.select.return_value.limit.return_value.where.return_value.execute.return_value = mock_members

        result = group_dao.get_all_groupmembers_by_group_id("test_group_id")

        assert result == mock_members
        mock_groupmember.select.assert_called_once()

    @patch("src.db.group_dao.Message")
    def test_get_all_messages_by_group_id(self, mock_message):
        """Test retrieving all messages by group id"""
        mock_msg1 = MagicMock()
        mock_msg2 = MagicMock()
        mock_messages = [mock_msg1, mock_msg2]

        mock_message.select.return_value.order_by.return_value.where.return_value.paginate.return_value.execute.return_value = mock_messages

        result = group_dao.get_all_messages_by_group_id("test_group_id", 1, 10)

        assert result == mock_messages
        mock_message.select.assert_called_once()
