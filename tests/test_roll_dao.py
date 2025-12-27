from unittest.mock import MagicMock, patch

from peewee import DoesNotExist

from src.db import roll_dao


class TestRollDao:
    @patch("src.db.roll_dao.Group")
    @patch("src.db.roll_dao.Roll")
    def test_get_roll_by_group_id_success(self, mock_roll, mock_group):
        """Test successful retrieval of roll by group id"""
        mock_group_instance = MagicMock()
        mock_group.get.return_value = mock_group_instance
        mock_roll_instance = MagicMock()
        mock_roll.get.return_value = mock_roll_instance

        result = roll_dao.get_roll_by_group_id("test_group_id")

        assert result == mock_roll_instance
        mock_group.get.assert_called_once()
        mock_roll.get.assert_called_once()

    @patch("src.db.roll_dao.Group")
    @patch("src.db.roll_dao.Roll")
    def test_get_roll_by_group_id_group_not_exists(self, mock_roll, mock_group):
        """Test when group doesn't exist"""
        mock_group.get.side_effect = DoesNotExist()

        result = roll_dao.get_roll_by_group_id("nonexistent_group")

        assert result is None
        mock_roll.get.assert_not_called()

    @patch("src.db.roll_dao.Group")
    @patch("src.db.roll_dao.Roll")
    def test_get_roll_by_group_id_roll_not_exists(self, mock_roll, mock_group):
        """Test when roll doesn't exist for group"""
        mock_group_instance = MagicMock()
        mock_group.get.return_value = mock_group_instance
        mock_roll.get.side_effect = DoesNotExist()

        result = roll_dao.get_roll_by_group_id("test_group_id")

        assert result is None
