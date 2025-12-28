import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Chat, Message, User
from telegram.ext import ContextTypes

from src.bot.handlers import remind


@pytest.fixture
def mock_update_remind():
    """Create a mock Telegram Update object for remind handler."""
    user = MagicMock(spec=User)
    user.id = 123456
    user.username = "testuser"

    chat = MagicMock(spec=Chat)
    chat.id = -1001234567890
    chat.type = "group"

    message = MagicMock(spec=Message)
    message.message_id = 1
    message.from_user = user
    message.chat = chat
    message.chat_id = -1001234567890
    message.text = "/remind 5m test"
    message.reply_to_message = None
    message.reply_text = AsyncMock()

    update = MagicMock()
    update.message = message

    return update


@pytest.fixture
def mock_context_remind():
    """Create a mock ContextTypes object for remind handler."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    context.job_queue = MagicMock()
    return context


class TestBuildJobName:
    def test_build_job_name_basic(self):
        result = remind.build_job_name("123456", "789", 1)
        assert "123456" in result and "789" in result and "1" in result

    def test_build_job_name_string_conversion(self):
        result = remind.build_job_name(123456, 789, 1)
        assert "123456" in result and "789" in result and "1" in result


class TestParseReminderDue:
    def test_parse_reminder_due_minutes(self):
        result = remind.parse_reminder_due(["5", "m"])
        assert result == 300

    def test_parse_reminder_due_minutes_short(self):
        result = remind.parse_reminder_due(["5", "min"])
        assert result == 300

    def test_parse_reminder_due_hours(self):
        result = remind.parse_reminder_due(["2", "h"])
        assert result == 7200

    def test_parse_reminder_due_hours_full(self):
        result = remind.parse_reminder_due(["2", "hours"])
        assert result == 7200

    def test_parse_reminder_due_days(self):
        result = remind.parse_reminder_due(["1", "d"])
        assert result == 86400

    def test_parse_reminder_due_combined(self):
        result = remind.parse_reminder_due(["1", "h", "30", "m"])
        assert result == 5400

    def test_parse_reminder_due_concatenated(self):
        result = remind.parse_reminder_due(["5m"])
        assert result == 300

    def test_parse_reminder_due_empty(self):
        result = remind.parse_reminder_due([])
        assert result == 0

    def test_parse_reminder_due_non_digit(self):
        result = remind.parse_reminder_due(["test"])
        assert result == 0


class TestExtractReminderMessage:
    def test_extract_reminder_message_with_quotes(self):
        message = '/remind 5m "test message"'
        result = remind.extract_reminder_message(message)
        assert result == "test message"

    def test_extract_reminder_message_no_quotes(self):
        message = "/remind 5m test"
        result = remind.extract_reminder_message(message)
        assert result == ""

    def test_extract_reminder_message_multiple_quotes(self):
        message = '/remind 5m "first" "second"'
        result = remind.extract_reminder_message(message)
        assert result == "first second"

    def test_extract_reminder_message_empty(self):
        message = ""
        result = remind.extract_reminder_message(message)
        assert result == ""


class TestRemoveJobIfExists:
    def test_remove_job_if_exists(self, mock_context_remind):
        """Test that remove_job_if_exists removes existing jobs."""
        mock_job = MagicMock()
        mock_job.schedule_removal = MagicMock()
        mock_context_remind.job_queue.get_jobs_by_name.return_value = [mock_job]

        result = remind.remove_job_if_exists("test_job", mock_context_remind)

        assert result is True
        mock_job.schedule_removal.assert_called_once()

    def test_remove_job_if_not_exists(self, mock_context_remind):
        """Test that remove_job_if_exists returns False for non-existent jobs."""
        mock_context_remind.job_queue.get_jobs_by_name.return_value = []

        result = remind.remove_job_if_exists("nonexistent_job", mock_context_remind)

        assert result is False
        mock_context_remind.job_queue.get_jobs_by_name.assert_called_once_with("nonexistent_job")


@pytest.mark.asyncio
class TestHandle:
    async def test_handle_too_many_reminders(self, mock_update_remind, mock_context_remind):
        """Test handle when user has too many reminders."""
        mock_update_remind.message.reply_to_message = None
        mock_context_remind.args = ["5", "m"]

        with (
            patch("src.bot.handlers.defaults.dc"),
            patch("src.bot.handlers.remind.scheduledjob_dao") as mock_scheduledjob_dao,
        ):
            mock_scheduledjob_dao.get_scheduledjobs_by_bakchod.return_value = list(range(11))

            await remind.handle(mock_update_remind, mock_context_remind)

            mock_update_remind.message.reply_text.assert_called()
            assert (
                "too many reminders"
                in mock_update_remind.message.reply_text.call_args.kwargs["text"]
            )

    async def test_handle_invalid_due_seconds(self, mock_update_remind, mock_context_remind):
        """Test handle with invalid due seconds (zero or negative)."""
        mock_update_remind.message.reply_to_message = None
        mock_context_remind.args = []

        with (
            patch("src.bot.handlers.defaults.dc"),
            patch("src.bot.handlers.remind.scheduledjob_dao") as mock_scheduledjob_dao,
            patch("src.bot.handlers.remind.parse_reminder_due") as mock_parse,
        ):
            mock_scheduledjob_dao.get_scheduledjobs_by_bakchod.return_value = []
            mock_parse.return_value = 0

            await remind.handle(mock_update_remind, mock_context_remind)

            mock_update_remind.message.reply_text.assert_called()

    async def test_handle_due_seconds_too_large(self, mock_update_remind, mock_context_remind):
        """Test handle with due seconds > 10 years."""
        mock_update_remind.message.reply_to_message = None
        mock_context_remind.args = []

        with (
            patch("src.bot.handlers.defaults.dc"),
            patch("src.bot.handlers.remind.scheduledjob_dao") as mock_scheduledjob_dao,
            patch("src.bot.handlers.remind.parse_reminder_due") as mock_parse,
            patch("src.bot.handlers.remind.util") as mock_util,
        ):
            mock_scheduledjob_dao.get_scheduledjobs_by_bakchod.return_value = []
            mock_parse.return_value = 10 * 365 * 86400
            mock_util.pretty_time_delta.return_value = "10 years"

            await remind.handle(mock_update_remind, mock_context_remind)

            mock_update_remind.message.reply_sticker.assert_called()

    async def test_handle_successful_reminder_creation(
        self, mock_update_remind, mock_context_remind
    ):
        """Test successful creation of a reminder."""
        mock_update_remind.message.reply_to_message = None
        mock_update_remind.message.text = '/remind 5m "test message"'
        mock_context_remind.args = ["5", "m"]
        mock_context_remind.job_queue.run_once = MagicMock()

        with (
            patch("src.bot.handlers.defaults.dc"),
            patch("src.bot.handlers.remind.scheduledjob_dao") as mock_scheduledjob_dao,
            patch("src.bot.handlers.remind.Bakchod") as mock_bakchod_class,
            patch("src.bot.handlers.remind.ScheduledJob") as mock_scheduledjob_class,
            patch("src.bot.handlers.remind.json.dumps") as mock_json_dumps,
            patch("src.bot.handlers.remind.util") as mock_util,
        ):
            mock_scheduledjob_dao.get_scheduledjobs_by_bakchod.return_value = []
            mock_bakchod_instance = MagicMock()
            mock_bakchod_class.get_by_id.return_value = mock_bakchod_instance
            mock_scheduledjob_instance = MagicMock()
            mock_scheduledjob_instance.job_id = 123
            mock_scheduledjob_class.create.return_value = mock_scheduledjob_instance
            mock_json_dumps.return_value = "mock_json"
            mock_util.pretty_time_delta.return_value = "5 minutes"

            await remind.handle(mock_update_remind, mock_context_remind)

            mock_scheduledjob_class.create.assert_called_once()
            mock_scheduledjob_instance.save.assert_called_once()
            mock_context_remind.job_queue.run_once.assert_called_once()
            mock_update_remind.message.reply_text.assert_called_once()


@pytest.mark.asyncio
class TestReminderHandler:
    async def test_reminder_handler_with_message(self, mock_context_remind):
        """Test reminder_handler with a custom reminder message."""
        mock_job = MagicMock()
        job_context = {
            "chat_id": -1001234567890,
            "reply_to_message_id": 1,
            "reminder_message": "Test reminder",
            "job_id": 123,
        }
        mock_job.data = json.dumps(job_context)
        mock_context_remind.job = mock_job

        with patch("src.bot.handlers.remind.ScheduledJob") as mock_scheduledjob_class:
            await remind.reminder_handler(mock_context_remind)

            mock_context_remind.bot.send_message.assert_called_once()
            assert "Test reminder" in mock_context_remind.bot.send_message.call_args[1]["text"]
            mock_scheduledjob_class.delete_by_id.assert_called_once_with(123)

    async def test_reminder_handler_without_message(self, mock_context_remind):
        """Test reminder_handler without a custom reminder message."""
        mock_job = MagicMock()
        job_context = {
            "chat_id": -1001234567890,
            "reply_to_message_id": 1,
            "reminder_message": "",
            "job_id": 123,
        }
        mock_job.data = json.dumps(job_context)
        mock_context_remind.job = mock_job

        with patch("src.bot.handlers.remind.ScheduledJob") as mock_scheduledjob_class:
            await remind.reminder_handler(mock_context_remind)

            mock_context_remind.bot.send_message.assert_called_once()
            mock_scheduledjob_class.delete_by_id.assert_called_once_with(123)

    async def test_reminder_handler_exception(self, mock_context_remind):
        """Test reminder_handler handles exceptions gracefully."""
        mock_job = MagicMock()
        mock_job.data = "invalid json"
        mock_context_remind.job = mock_job

        with patch("src.bot.handlers.remind.ScheduledJob") as mock_scheduledjob_class:
            await remind.reminder_handler(mock_context_remind)

            mock_scheduledjob_class.delete_by_id.assert_not_called()
