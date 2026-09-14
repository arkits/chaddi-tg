import datetime
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram.constants import ParseMode
from telegram.error import BadRequest, Forbidden

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

    @patch("src.domain.scheduler.util")
    @patch("src.domain.scheduler.Group")
    @patch("src.domain.scheduler.Quote")
    @pytest.mark.anyio
    async def test_daily_post_callback_with_enabled_groups(
        self, mock_quote_class, mock_group_class, mock_util
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
        mock_util.extract_pretty_name_from_bakchod.return_value = "@testauthor"

        mock_context = MagicMock()
        mock_context.bot.send_message = MagicMock()

        await scheduler.daily_post_callback(mock_context)

        assert mock_context.bot.send_message.called
        call_args = mock_context.bot.send_message.call_args
        assert call_args[1]["chat_id"] == "test_group_id"
        assert call_args[1]["parse_mode"] == ParseMode.HTML

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

    @patch("src.domain.scheduler.util")
    @patch("src.domain.scheduler.Group")
    @patch("src.domain.scheduler.Quote")
    @pytest.mark.anyio
    async def test_daily_post_callback_send_failure(
        self, mock_quote_class, mock_group_class, mock_util
    ):
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
        mock_util.extract_pretty_name_from_bakchod.return_value = "Test Author"

        mock_context = MagicMock()
        mock_context.bot.send_message.side_effect = Exception("Send failed")

        await scheduler.daily_post_callback(mock_context)

        assert mock_context.bot.send_message.called

    @pytest.mark.parametrize(
        "error_cls,error_arg", [(BadRequest, "Chat not found"), (Forbidden, "Bot was kicked")]
    )
    @patch("src.domain.scheduler.util")
    @patch("src.domain.scheduler.Group")
    @patch("src.domain.scheduler.Quote")
    @pytest.mark.anyio
    async def test_daily_post_callback_disables_group_on_unreachable_chat(
        self, mock_quote_class, mock_group_class, mock_util, error_cls, error_arg
    ):
        """Test that an unreachable chat (kicked/deleted) disables good_morning for that group."""
        mock_group = MagicMock()
        mock_group.group_id = "test_group_id"
        mock_group.name = "Test Group"
        mock_group.metadata = {"good_morning_enabled": True}
        mock_group_class.select.return_value = [mock_group]

        mock_quote_class.select.return_value.order_by.return_value.limit.return_value.first.return_value = None

        mock_context = MagicMock()
        mock_context.bot.send_message.side_effect = error_cls(error_arg)

        await scheduler.daily_post_callback(mock_context)

        assert mock_group.metadata["good_morning_enabled"] is False
        assert mock_group.save.called

    @patch("src.domain.scheduler.util")
    @patch("src.domain.scheduler.Group")
    @patch("src.domain.scheduler.Quote")
    @pytest.mark.anyio
    async def test_daily_post_callback_message_includes_quote_date(
        self, mock_quote_class, mock_group_class, mock_util
    ):
        """The posted message includes the quote text, author, and the date it was captured."""
        mock_group = MagicMock()
        mock_group.group_id = "test_group_id"
        mock_group.name = "Test Group"
        mock_group.metadata = {"good_morning_enabled": True}
        mock_group_class.select.return_value = [mock_group]

        mock_quote = MagicMock()
        mock_quote.quote_id = "quote_1"
        mock_quote.text = "Test quote text"
        mock_quote.created = datetime.datetime(2026, 3, 12)
        mock_quote_class.select.return_value.where.return_value.order_by.return_value.limit.return_value.first.return_value = mock_quote
        mock_util.extract_pretty_name_from_bakchod.return_value = "Test Author"

        mock_context = MagicMock()
        mock_context.bot.send_message = AsyncMock()

        await scheduler.daily_post_callback(mock_context)

        message_text = mock_context.bot.send_message.call_args[1]["text"]
        assert "Test quote text" in message_text
        assert "Test Author" in message_text
        assert "12 Mar 2026" in message_text

    def test_prune_recent_quotes_removes_old_entries(self):
        """Entries older than the 2-week window are dropped."""
        now = int(time.time())
        recent_quotes = {
            "old_quote": now - scheduler.RECENT_QUOTE_WINDOW_SECONDS - 3600,
            "fresh_quote": now - 3600,
        }

        pruned = scheduler._prune_recent_quotes(recent_quotes, now)

        assert pruned == {"fresh_quote": now - 3600}

    @patch("src.domain.scheduler.util")
    @patch("src.domain.scheduler.Group")
    @patch("src.domain.scheduler.Quote")
    @pytest.mark.anyio
    async def test_daily_post_callback_excludes_recently_posted_quotes(
        self, mock_quote_class, mock_group_class, mock_util
    ):
        """Quotes posted within the past 2 weeks are excluded from selection."""
        now = int(time.time())
        mock_group = MagicMock()
        mock_group.group_id = "test_group_id"
        mock_group.name = "Test Group"
        mock_group.metadata = {
            "good_morning_enabled": True,
            "recent_quote_ids": {"recent_quote": now - 3600},
        }
        mock_group_class.select.return_value = [mock_group]

        mock_quote = MagicMock()
        mock_quote.quote_id = "fresh_quote"
        mock_quote.text = "Test quote text"
        mock_quote_class.select.return_value.where.return_value.order_by.return_value.limit.return_value.first.return_value = mock_quote
        mock_util.extract_pretty_name_from_bakchod.return_value = "@testauthor"

        mock_context = MagicMock()
        mock_context.bot.send_message = MagicMock()

        await scheduler.daily_post_callback(mock_context)

        where_call_args = mock_quote_class.select.return_value.where.call_args[0]
        mock_quote_class.quote_id.not_in.assert_called_once_with(["recent_quote"])
        assert where_call_args[1] == mock_quote_class.quote_id.not_in.return_value

    @patch("src.domain.scheduler.util")
    @patch("src.domain.scheduler.Group")
    @patch("src.domain.scheduler.Quote")
    @pytest.mark.anyio
    async def test_daily_post_callback_records_posted_quote(
        self, mock_quote_class, mock_group_class, mock_util
    ):
        """After a successful send, the posted quote is tracked with a timestamp."""
        mock_group = MagicMock()
        mock_group.group_id = "test_group_id"
        mock_group.name = "Test Group"
        mock_group.metadata = {"good_morning_enabled": True}
        mock_group_class.select.return_value = [mock_group]

        mock_quote = MagicMock()
        mock_quote.quote_id = "new_quote"
        mock_quote.text = "Test quote text"
        mock_quote_class.select.return_value.where.return_value.order_by.return_value.limit.return_value.first.return_value = mock_quote
        mock_util.extract_pretty_name_from_bakchod.return_value = "@testauthor"

        mock_context = MagicMock()
        mock_context.bot.send_message = AsyncMock()

        await scheduler.daily_post_callback(mock_context)

        assert "new_quote" in mock_group.metadata["recent_quote_ids"]
        assert mock_group.save.called

    @patch("src.domain.scheduler.util")
    @patch("src.domain.scheduler.Group")
    @patch("src.domain.scheduler.Quote")
    @pytest.mark.anyio
    async def test_daily_post_callback_falls_back_when_all_quotes_recent(
        self, mock_quote_class, mock_group_class, mock_util
    ):
        """If every quote was posted recently, fall back to repeating one rather than skipping."""
        mock_group = MagicMock()
        mock_group.group_id = "test_group_id"
        mock_group.name = "Test Group"
        mock_group.metadata = {
            "good_morning_enabled": True,
            "recent_quote_ids": {"only_quote": int(time.time()) - 3600},
        }
        mock_group_class.select.return_value = [mock_group]

        mock_quote = MagicMock()
        mock_quote.quote_id = "only_quote"
        mock_quote.text = "Test quote text"
        mock_quote_class.select.return_value.where.return_value.order_by.return_value.limit.return_value.first.side_effect = [
            None,
            mock_quote,
        ]
        mock_util.extract_pretty_name_from_bakchod.return_value = "@testauthor"

        mock_context = MagicMock()
        mock_context.bot.send_message = MagicMock()

        await scheduler.daily_post_callback(mock_context)

        assert mock_context.bot.send_message.called
        call_args = mock_context.bot.send_message.call_args
        assert "Test quote text" in call_args[1]["text"]

    def test_schedule_daily_posts(self, mock_job_queue):
        """Test scheduling daily good morning posts."""
        scheduler.schedule_daily_posts(mock_job_queue)

        mock_job_queue.run_daily.assert_called_once()

        call_args = mock_job_queue.run_daily.call_args
        assert call_args[0][0] == scheduler.daily_post_callback
        assert call_args[1]["name"] == "daily_good_morning"
        assert call_args[1]["time"].hour == 8
        assert call_args[1]["time"].minute == 0
