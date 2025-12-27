from unittest.mock import MagicMock, patch

import pytest
from telegram import Chat, Message, Update, User

from src.domain import dc


@pytest.fixture
def mock_update():
    """Create a mock Telegram Update object for testing."""
    user = MagicMock(spec=User)
    user.id = 123456
    user.username = "testuser"
    user.first_name = "Test"
    user.full_name = "Test User"

    chat = MagicMock(spec=Chat)
    chat.id = -1001234567890
    chat.type = "group"
    chat.title = "Test Group"

    message = MagicMock(spec=Message)
    message.message_id = 1
    message.from_user = user
    message.chat = chat
    message.text = "/test"

    update = MagicMock(spec=Update)
    update.message = message

    return update


@pytest.fixture
def mock_bakchod():
    """Create a mock Bakchod object for testing."""
    bakchod = MagicMock()
    bakchod.tg_id = 123456
    bakchod.username = "testuser"
    bakchod.pretty_name = "Test User"
    bakchod.rokda = 100.0
    return bakchod


@pytest.fixture
def mock_group():
    """Create a mock Group object for testing."""
    group = MagicMock()
    group.group_id = -1001234567890
    group.name = "Test Group"
    group.group_id = -1001234567890
    return group


def test_log_command_usage_with_valid_update(mock_update):
    """Test logging command usage with valid update."""
    with (
        patch("src.domain.dc.analytics") as _mock_analytics,
        patch("src.domain.dc.metrics") as _mock_sentry_metrics,
        patch("src.domain.dc.Bakchod") as mock_bakchod_model,
        patch("src.domain.dc.Group") as _mock_group_model,
        patch("src.domain.dc.CommandUsage") as _mock_command_usage,
        patch("src.domain.dc.prom_metrics") as _mock_prom_metrics,
        patch("src.domain.dc.sync_persistence_data") as mock_sync,
    ):
        mock_bakchod_model.get.return_value = MagicMock()
        _mock_group_model.get.return_value = MagicMock()
        _mock_command_usage.create.return_value = MagicMock()

        dc.log_command_usage("test_command", mock_update)

        assert mock_sync.called


def test_log_command_usage_without_message():
    """Test logging command usage when update has no message."""
    update = MagicMock(spec=Update)
    update.message = None

    result = dc.log_command_usage("test_command", update)

    assert result is None


def test_log_command_usage_with_database_error(mock_update):
    """Test logging command usage when database operations fail."""
    with (
        patch("src.domain.dc.analytics") as _mock_analytics,
        patch("src.domain.dc.metrics") as _mock_sentry_metrics,
        patch("src.domain.dc.Bakchod") as mock_bakchod_model,
        patch("src.domain.dc.Group") as _mock_group_model,
        patch("src.domain.dc.CommandUsage") as _mock_command_usage,
        patch("src.domain.dc.prom_metrics") as _mock_prom_metrics,
        patch("src.domain.dc.sync_persistence_data") as mock_sync,
    ):
        mock_bakchod_model.get.side_effect = Exception("Database error")

        dc.log_command_usage("test_command", mock_update)

        assert mock_sync.called


def test_sync_persistence_data_with_valid_update(mock_update):
    """Test syncing persistence data with valid update."""

    with (
        patch("src.domain.dc.bakchod_dao") as mock_bakchod_dao,
        patch("src.domain.dc.message_dao") as mock_message_dao,
        patch("src.domain.dc.group_dao") as mock_group_dao,
        patch("src.domain.dc.analytics") as _mock_analytics,
        patch("src.domain.dc.metrics") as _mock_sentry_metrics,
        patch("src.domain.dc.sio") as _mock_sio,
        patch("src.domain.dc.asyncio.create_task") as _mock_create_task,
    ):
        mock_bakchod = MagicMock()
        mock_bakchod_dao.get_or_create_bakchod_from_tg_user.return_value = mock_bakchod

        mock_message = MagicMock()
        mock_message_dao.log_message_from_update.return_value = mock_message

        mock_group_dao.log_group_from_update.return_value = MagicMock()

        dc.sync_persistence_data(mock_update)

        assert mock_bakchod.username == mock_update.message.from_user.username
        assert mock_bakchod.lastseen is not None
        assert mock_bakchod.save.called


def test_sync_persistence_data_without_from_user():
    """Test syncing persistence data when message has no from_user."""
    message = MagicMock(spec=Message)
    message.from_user = None
    message.chat = MagicMock()
    message.chat.id = 12345
    message.chat.type = "private"

    update = MagicMock(spec=Update)
    update.message = message

    with pytest.raises(AttributeError):
        dc.sync_persistence_data(update)


def test_sync_persistence_data_with_exception(mock_update):
    """Test syncing persistence data when an exception occurs."""
    with (
        patch("src.domain.dc.bakchod_dao") as mock_bakchod_dao,
        patch("src.domain.dc.analytics") as _mock_analytics,
        patch("src.domain.dc.metrics") as _mock_sentry_metrics,
    ):
        mock_bakchod_dao.get_or_create_bakchod_from_tg_user.side_effect = Exception(
            "Database error"
        )

        with pytest.raises(Exception):  # noqa: B017
            dc.sync_persistence_data(mock_update)
