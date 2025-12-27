import contextlib
import os
from unittest.mock import MagicMock, patch

import pytest
from peewee import DoesNotExist

from src.db import Bakchod
from src.domain.util import (
    acquire_external_resource,
    delete_file,
    extract_pretty_name_from_bakchod,
    get_random_bakchod_from_group,
    is_admin_tg_user,
    paywall_user,
)


class TestUtilAdvanced:
    def test_extract_pretty_name_from_bakchod_username(self):
        """Test extracting pretty name with username."""
        bakchod = MagicMock(spec=Bakchod)
        bakchod.username = "testuser"
        bakchod.pretty_name = None
        bakchod.tg_id = 123

        result = extract_pretty_name_from_bakchod(bakchod)

        assert result == "@testuser"

    def test_extract_pretty_name_from_bakchod_pretty_name(self):
        """Test extracting pretty name with pretty_name."""
        bakchod = MagicMock(spec=Bakchod)
        bakchod.username = None
        bakchod.pretty_name = "Test User"
        bakchod.tg_id = 123

        result = extract_pretty_name_from_bakchod(bakchod)

        assert result == "Test User"

    def test_extract_pretty_name_from_bakchod_tg_id_only(self):
        """Test extracting pretty name with only tg_id."""
        bakchod = MagicMock(spec=Bakchod)
        bakchod.username = None
        bakchod.pretty_name = None
        bakchod.tg_id = 123456

        result = extract_pretty_name_from_bakchod(bakchod)

        assert result == "123456"

    def test_extract_pretty_name_from_bakchod_all_none(self):
        """Test extracting pretty name when all fields are None."""
        bakchod = MagicMock(spec=Bakchod)
        bakchod.username = None
        bakchod.pretty_name = None
        bakchod.tg_id = None

        result = extract_pretty_name_from_bakchod(bakchod)

        assert result is None

    def test_delete_file_existing(self, tmp_path):
        """Test deleting an existing file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        assert test_file.exists()

        delete_file(str(test_file))

        assert not test_file.exists()

    def test_delete_file_nonexistent(self):
        """Test attempting to delete a non-existent file."""
        with patch("src.domain.util.logger") as mock_logger:
            delete_file("/nonexistent/path/file.txt")

            mock_logger.warning.assert_called()

    @patch("src.domain.util.requests")
    @patch("src.domain.util.os.path.exists")
    def test_acquire_external_resource_already_exists(self, mock_exists, mock_requests):
        """Test acquiring resource that already exists locally."""
        mock_exists.return_value = True

        result = acquire_external_resource("http://example.com/file.txt", "file.txt")

        assert result == os.path.join("resources", "external", "file.txt")
        mock_requests.get.assert_not_called()

    @patch("src.domain.util.requests")
    @patch("src.domain.util.os.path.exists")
    @patch("src.domain.util.open")
    def test_acquire_external_resource_download(
        self, mock_open, mock_exists, mock_requests, tmp_path
    ):
        """Test acquiring and downloading a resource."""
        mock_exists.return_value = False
        mock_response = MagicMock()
        mock_response.content = b"test content"
        mock_response.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_response

        result = acquire_external_resource("http://example.com/file.txt", "file.txt")

        expected_path = os.path.join("resources", "external", "file.txt")
        assert result == expected_path
        mock_requests.get.assert_called_once()
        mock_open.assert_called_once()

    @patch("src.domain.util.requests")
    @patch("src.domain.util.os.path.exists")
    @patch("src.domain.util.open")
    def test_acquire_external_resource_http_error(self, mock_open, mock_exists, mock_requests):
        """Test acquiring resource when HTTP error occurs."""
        mock_exists.return_value = False
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 404")
        mock_requests.get.return_value = mock_response

        with patch("src.domain.util.logger"), contextlib.suppress(Exception):
            acquire_external_resource("http://example.com/file.txt", "file.txt")

    @patch("src.domain.util.ADMIN_IDS", ["123456", "789012"])
    def test_is_admin_tg_user_admin(self):
        """Test checking if user is admin."""
        user = MagicMock()
        user.id = 123456

        result = is_admin_tg_user(user)

        assert result is True

    @patch("src.domain.util.ADMIN_IDS", ["123456", "789012"])
    def test_is_admin_tg_user_not_admin(self):
        """Test checking if user is not admin."""
        user = MagicMock()
        user.id = 999999

        result = is_admin_tg_user(user)

        assert result is False

    @patch("src.domain.util.Bakchod")
    def test_paywall_user_sufficient_rokda(self, mock_bakchod_model):
        """Test paywall when user has sufficient rokda."""
        mock_bakchod = MagicMock()
        mock_bakchod.rokda = 100.0
        mock_bakchod_model.get_by_id.return_value = mock_bakchod

        result = paywall_user("user123", 50.0)

        assert result is True
        assert mock_bakchod.rokda == 50.0
        assert mock_bakchod.save.called

    @patch("src.domain.util.Bakchod")
    def test_paywall_user_insufficient_rokda(self, mock_bakchod_model):
        """Test paywall when user has insufficient rokda."""
        mock_bakchod = MagicMock()
        mock_bakchod.rokda = 30.0
        mock_bakchod_model.get_by_id.return_value = mock_bakchod

        result = paywall_user("user123", 50.0)

        assert result is False
        assert mock_bakchod.rokda == 30.0
        assert not mock_bakchod.save.called

    @patch("src.domain.util.Bakchod")
    def test_paywall_user_exact_rokda(self, mock_bakchod_model):
        """Test paywall when user has exactly the required rokda."""
        mock_bakchod = MagicMock()
        mock_bakchod.rokda = 50.0
        mock_bakchod_model.get_by_id.return_value = mock_bakchod

        result = paywall_user("user123", 50.0)

        assert result is False  # rokda <= cost returns False
        assert mock_bakchod.rokda == 50.0
        assert not mock_bakchod.save.called

    @patch("src.domain.util.Bakchod")
    def test_paywall_user_not_found(self, mock_bakchod_model):
        """Test paywall when bakchod is not found - raises DoesNotExist."""
        mock_bakchod_model.get_by_id.side_effect = DoesNotExist()

        from peewee import DoesNotExist as PeeweeDoesNotExist

        with pytest.raises(PeeweeDoesNotExist):
            paywall_user("nonexistent", 50.0)

    @patch("src.domain.util.GroupMember")
    @patch("src.domain.util.choose_random_element_from_list")
    @patch("src.domain.util.Bakchod")
    def test_get_random_bakchod_from_group_success(
        self, mock_bakchod, mock_random_choose, mock_groupmember
    ):
        """Test getting random bakchod from group."""
        mock_groupmember_instance = MagicMock()
        mock_groupmember_instance.bakchod_id = "user123"
        mock_groupmember.select.return_value.where.return_value.execute.return_value = [
            mock_groupmember_instance
        ]
        mock_random_choose.return_value = mock_groupmember_instance

        mock_bakchod_instance = MagicMock()
        mock_bakchod_instance.username = "testuser"
        mock_bakchod.get_by_id.return_value = mock_bakchod_instance

        result = get_random_bakchod_from_group("group123", "avoid_me")

        assert result == mock_bakchod_instance
        mock_bakchod.get_by_id.assert_called_with("user123")

    @patch("src.domain.util.GroupMember")
    @patch("src.domain.util.choose_random_element_from_list")
    def test_get_random_bakchod_from_group_no_members(self, mock_random_choose, mock_groupmember):
        """Test getting random bakchod when group has no members."""
        mock_groupmember.select.return_value.where.return_value.execute.return_value = []
        mock_random_choose.return_value = None

        result = get_random_bakchod_from_group("empty_group", "")

        assert result is None
