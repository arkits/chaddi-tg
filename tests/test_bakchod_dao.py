from unittest.mock import MagicMock, patch

from peewee import DoesNotExist

from src.db import bakchod_dao


class TestBakchodDao:
    @patch("src.db.bakchod_dao.Bakchod")
    def test_get_bakchod_from_update_existing(self, mock_bakchod):
        """Test retrieving existing bakchod from update."""
        mock_bakchod_instance = MagicMock()
        mock_bakchod.get.return_value = mock_bakchod_instance

        mock_user = MagicMock()
        mock_user.id = "test_id"
        mock_user.username = "testuser"
        mock_user.first_name = "Test"

        mock_message = MagicMock()
        mock_message.from_user = mock_user

        mock_update = MagicMock()
        mock_update.message = mock_update.message
        mock_update.message = mock_message

        result = bakchod_dao.get_bakchod_from_update(mock_update)

        assert result == mock_bakchod_instance
        mock_bakchod.get.assert_called_once()

    @patch("src.db.bakchod_dao.Bakchod")
    def test_get_bakchod_from_update_new(self, mock_bakchod):
        """Test creating new bakchod from update."""
        mock_bakchod.get.side_effect = DoesNotExist()

        mock_bakchod_instance = MagicMock()
        mock_bakchod.create.return_value = mock_bakchod_instance

        mock_user = MagicMock()
        mock_user.id = "test_id"
        mock_user.username = "testuser"
        mock_user.first_name = "Test"

        mock_message = MagicMock()
        mock_message.from_user = mock_user

        mock_update = MagicMock()
        mock_update.message = mock_message

        result = bakchod_dao.get_bakchod_from_update(mock_update)

        assert result == mock_bakchod_instance
        mock_bakchod.create.assert_called_once()

    @patch("src.db.bakchod_dao.Bakchod")
    def test_get_or_create_bakchod_from_tg_user_existing(self, mock_bakchod):
        """Test retrieving existing bakchod from Telegram user."""
        mock_bakchod_instance = MagicMock()
        mock_bakchod.get.return_value = mock_bakchod_instance

        mock_user = MagicMock()
        mock_user.id = "test_id"
        mock_user.username = "testuser"
        mock_user.first_name = "Test"

        result = bakchod_dao.get_or_create_bakchod_from_tg_user(mock_user)

        assert result == mock_bakchod_instance
        mock_bakchod.get.assert_called_once()
        mock_bakchod.create.assert_not_called()

    @patch("src.db.bakchod_dao.Bakchod")
    def test_get_or_create_bakchod_from_tg_user_new(self, mock_bakchod):
        """Test creating new bakchod from Telegram user."""
        mock_bakchod.get.side_effect = DoesNotExist()

        mock_bakchod_instance = MagicMock()
        mock_bakchod.create.return_value = mock_bakchod_instance

        mock_user = MagicMock()
        mock_user.id = "test_id"
        mock_user.username = "testuser"
        mock_user.first_name = "Test"

        result = bakchod_dao.get_or_create_bakchod_from_tg_user(mock_user)

        assert result == mock_bakchod_instance
        mock_bakchod.create.assert_called_once()

    @patch("src.db.bakchod_dao.Bakchod")
    def test_get_bakchod_by_username_success(self, mock_bakchod):
        """Test successful retrieval of bakchod by username."""
        mock_bakchod_instance = MagicMock()
        mock_bakchod_instance.username = "testuser"
        mock_bakchod.get.return_value = mock_bakchod_instance

        result = bakchod_dao.get_bakchod_by_username("testuser")

        assert result == mock_bakchod_instance
        mock_bakchod.get.assert_called_once()

    @patch("src.db.bakchod_dao.Bakchod")
    def test_get_bakchod_by_username_not_exists(self, mock_bakchod):
        """Test when bakchod doesn't exist with username."""
        mock_bakchod.get.side_effect = DoesNotExist()

        result = bakchod_dao.get_bakchod_by_username("nonexistent")

        assert result is None
