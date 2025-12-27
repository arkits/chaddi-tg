import time
from unittest.mock import MagicMock, patch

import pytest

from src.domain import scheduler


@pytest.fixture
def mock_job_queue():
    """Create a mock JobQueue for testing."""
    job_queue = MagicMock()
    return job_queue


@pytest.fixture
def mock_scheduled_jobs():
    """Create mock scheduled jobs for testing."""
    jobs = []

    # Job in the future
    job1 = MagicMock()
    job1.job_context = {
        "reminder_time": int(time.time()) + 3600,  # 1 hour in the future
        "chat_id": "test_chat_1",
        "from_bakchod_id": "user1",
        "job_id": "job1",
    }
    jobs.append(job1)

    # Job in the past (should be skipped)
    job2 = MagicMock()
    job2.job_context = {
        "reminder_time": int(time.time()) - 3600,  # 1 hour in the past
        "chat_id": "test_chat_2",
        "from_bakchod_id": "user2",
        "job_id": "job2",
    }
    jobs.append(job2)

    return jobs


class TestScheduler:
    @patch("src.domain.scheduler.ScheduledJob")
    def test_reschedule_saved_jobs_with_future_job(self, mock_scheduled_job_class, mock_job_queue):
        """Test rescheduling jobs that are in the future."""
        job1 = MagicMock()
        job1.job_context = {
            "reminder_time": int(time.time()) + 7200,
            "chat_id": "test_chat",
            "from_bakchod_id": "user123",
            "job_id": "job123",
        }
        mock_scheduled_job_class.select.return_value = [job1]

        scheduler.reschedule_saved_jobs(mock_job_queue)

        mock_job_queue.run_once.assert_called_once()
        assert not job1.delete_instance.called

    @patch("src.domain.scheduler.ScheduledJob")
    def test_reschedule_saved_jobs_skips_past_jobs(self, mock_scheduled_job_class, mock_job_queue):
        """Test that past jobs are skipped and deleted."""
        job1 = MagicMock()
        job1.job_context = {
            "reminder_time": int(time.time()) - 3600,
            "chat_id": "test_chat",
            "from_bakchod_id": "user123",
            "job_id": "job123",
        }
        mock_scheduled_job_class.select.return_value = [job1]

        scheduler.reschedule_saved_jobs(mock_job_queue)

        assert job1.delete_instance.called
        mock_job_queue.run_once.assert_not_called()

    @patch("src.domain.scheduler.ScheduledJob")
    def test_reschedule_saved_jobs_mixed(self, mock_scheduled_job_class, mock_job_queue):
        """Test rescheduling with a mix of future and past jobs."""
        job_future = MagicMock()
        job_future.job_context = {
            "reminder_time": int(time.time()) + 3600,
            "chat_id": "chat_future",
            "from_bakchod_id": "user_future",
            "job_id": "job_future",
        }

        job_past = MagicMock()
        job_past.job_context = {
            "reminder_time": int(time.time()) - 3600,
            "chat_id": "chat_past",
            "from_bakchod_id": "user_past",
            "job_id": "job_past",
        }

        mock_scheduled_job_class.select.return_value = [job_future, job_past]

        scheduler.reschedule_saved_jobs(mock_job_queue)

        assert mock_job_queue.run_once.call_count == 1
        assert job_past.delete_instance.called

    @patch("src.domain.scheduler.ScheduledJob")
    def test_reschedule_saved_jobs_empty(self, mock_scheduled_job_class, mock_job_queue):
        """Test rescheduling with no jobs."""
        mock_scheduled_job_class.select.return_value = []

        scheduler.reschedule_saved_jobs(mock_job_queue)

        mock_job_queue.run_once.assert_not_called()

    @patch("src.domain.scheduler.Group")
    @pytest.mark.anyio
    async def test_daily_post_callback_no_enabled_groups(self, mock_group_class):
        """Test daily post callback when no groups have good morning enabled."""
        mock_group_class.select.return_value = []

        mock_context = MagicMock()
        mock_context.bot.send_message = MagicMock()

        await scheduler.daily_post_callback(mock_context)

        mock_context.bot.send_message.assert_not_called()

    @patch("src.domain.scheduler.Group")
    @patch("src.domain.scheduler.Quote")
    @pytest.mark.anyio
    async def test_daily_post_callback_with_enabled_groups(
        self, mock_quote_class, mock_group_class
    ):
        """Test daily post callback with enabled groups."""
        # Mock group with good morning enabled
        mock_group = MagicMock()
        mock_group.group_id = "test_group_id"
        mock_group.name = "Test Group"
        mock_group.metadata = {"good_morning_enabled": True}
        mock_group_class.select.return_value = [mock_group]

        # Mock quote
        mock_quote = MagicMock()
        mock_quote.text = "Test quote text"
        mock_author = MagicMock()
        mock_author.pretty_name = "Test Author"
        mock_author.username = "testauthor"
        mock_quote.author_bakchod = mock_author
        mock_quote_class.select.return_value.order_by.return_value.limit.return_value.first.return_value = mock_quote

        mock_context = MagicMock()
        mock_context.bot.send_message = MagicMock()

        await scheduler.daily_post_callback(mock_context)

        assert mock_context.bot.send_message.called
        call_args = mock_context.bot.send_message.call_args
        assert call_args[1]["chat_id"] == "test_group_id"

    @patch("src.domain.scheduler.Group")
    @patch("src.domain.scheduler.Quote")
    @pytest.mark.anyio
    async def test_daily_post_callback_without_quote(self, mock_quote_class, mock_group_class):
        """Test daily post callback when no quote is available."""
        # Mock group with good morning enabled
        mock_group = MagicMock()
        mock_group.group_id = "test_group_id"
        mock_group.name = "Test Group"
        mock_group.metadata = {"good_morning_enabled": True}
        mock_group_class.select.return_value = [mock_group]

        # No quote available
        mock_quote_class.select.return_value.order_by.return_value.limit.return_value.first.return_value = None

        mock_context = MagicMock()
        mock_context.bot.send_message = MagicMock()

        await scheduler.daily_post_callback(mock_context)

        assert mock_context.bot.send_message.called
        call_args = mock_context.bot.send_message.call_args
        assert call_args[1]["chat_id"] == "test_group_id"

    @patch("src.domain.scheduler.Group")
    @patch("src.domain.scheduler.Quote")
    @pytest.mark.anyio
    async def test_daily_post_callback_send_failure(self, mock_quote_class, mock_group_class):
        """Test daily post callback when sending message fails."""
        mock_group = MagicMock()
        mock_group.group_id = "test_group_id"
        mock_group.name = "Test Group"
        mock_group.metadata = {"good_morning_enabled": True}
        mock_group_class.select.return_value = [mock_group]

        mock_quote = MagicMock()
        mock_quote.text = "Test quote"
        mock_author = MagicMock()
        mock_author.pretty_name = "Test Author"
        mock_author.username = None
        mock_quote.author_bakchod = mock_author
        mock_quote_class.select.return_value.order_by.return_value.limit.return_value.first.return_value = mock_quote

        mock_context = MagicMock()
        mock_context.bot.send_message.side_effect = Exception("Send failed")

        await scheduler.daily_post_callback(mock_context)

        assert mock_context.bot.send_message.called

    def test_schedule_daily_posts(self, mock_job_queue):
        """Test scheduling daily good morning posts."""
        scheduler.schedule_daily_posts(mock_job_queue)

        mock_job_queue.run_daily.assert_called_once()

        call_args = mock_job_queue.run_daily.call_args
        assert call_args[0][0] == scheduler.daily_post_callback
        assert call_args[1]["name"] == "daily_good_morning"
        assert call_args[1]["time"].hour == 8
        assert call_args[1]["time"].minute == 0
