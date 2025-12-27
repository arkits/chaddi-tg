from unittest.mock import MagicMock, patch

from peewee import DoesNotExist

from src.db import scheduledjob_dao


class TestScheduledJobDao:
    @patch("src.db.scheduledjob_dao.Bakchod")
    @patch("src.db.scheduledjob_dao.ScheduledJob")
    def test_get_scheduledjobs_by_bakchod_success(self, mock_scheduled_job, mock_bakchod):
        """Test successful retrieval of scheduled jobs by bakchod id"""
        mock_bakchod_instance = MagicMock()
        mock_bakchod.get_by_id.return_value = mock_bakchod_instance

        mock_job1 = MagicMock()
        mock_job1.id = 1
        mock_job2 = MagicMock()
        mock_job2.id = 2
        mock_query_result = [mock_job1, mock_job2]

        mock_scheduled_job.select.return_value.where.return_value.execute.return_value = (
            mock_query_result
        )

        result = scheduledjob_dao.get_scheduledjobs_by_bakchod("test_bakchod_id")

        assert result is not None
        assert len(result) == 2
        mock_bakchod.get_by_id.assert_called_once_with("test_bakchod_id")

    @patch("src.db.scheduledjob_dao.Bakchod")
    @patch("src.db.scheduledjob_dao.ScheduledJob")
    def test_get_scheduledjobs_by_bakchod_not_exists(self, mock_scheduled_job, mock_bakchod):
        """Test when bakchod doesn't exist"""
        mock_bakchod.get_by_id.side_effect = DoesNotExist()

        result = scheduledjob_dao.get_scheduledjobs_by_bakchod("nonexistent_bakchod")

        assert result is None
        mock_scheduled_job.select.assert_not_called()

    @patch("src.db.scheduledjob_dao.Bakchod")
    @patch("src.db.scheduledjob_dao.ScheduledJob")
    def test_get_scheduledjobs_by_bakchod_no_jobs(self, mock_scheduled_job, mock_bakchod):
        """Test when bakchod has no scheduled jobs"""
        mock_bakchod_instance = MagicMock()
        mock_bakchod.get_by_id.return_value = mock_bakchod_instance

        mock_scheduled_job.select.return_value.where.return_value.execute.return_value = []

        result = scheduledjob_dao.get_scheduledjobs_by_bakchod("test_bakchod_id")

        assert result is not None
        assert len(result) == 0
