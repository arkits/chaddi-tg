from unittest.mock import MagicMock, patch

from src.domain import metrics


class TestMetrics:
    def test_inc_message_count(self):
        """Test that inc_message_count increments the counter"""
        mock_update = MagicMock()
        mock_update.message.chat.id = "test_group_123"
        mock_update.message.chat.title = "Test Group"

        with patch.object(metrics.messages_count, "labels") as mock_labels:
            mock_counter = MagicMock()
            mock_labels.return_value = mock_counter

            metrics.inc_message_count(mock_update)

            mock_labels.assert_called_once_with(group_id="test_group_123", group_name="Test Group")
            mock_counter.inc.assert_called_once()

    def test_inc_command_usage_count(self):
        """Test that inc_command_usage_count increments the counter"""
        mock_update = MagicMock()
        mock_update.message.chat.id = "test_group_456"
        mock_update.message.chat.title = "Test Group 2"

        with patch.object(metrics.command_usage_count, "labels") as mock_labels:
            mock_counter = MagicMock()
            mock_labels.return_value = mock_counter

            metrics.inc_command_usage_count("/test", mock_update)

            mock_labels.assert_called_once_with(
                group_id="test_group_456", group_name="Test Group 2", command_name="/test"
            )
            mock_counter.inc.assert_called_once()

    def test_messages_count_counter_initialized(self):
        """Test that messages_count counter is properly initialized"""
        assert metrics.messages_count._name == "chaddi_messages_count"
        assert len(metrics.messages_count._labelnames) == 2
        assert "group_id" in metrics.messages_count._labelnames
        assert "group_name" in metrics.messages_count._labelnames

    def test_command_usage_count_counter_initialized(self):
        """Test that command_usage_count counter is properly initialized"""
        assert metrics.command_usage_count._name == "chaddi_command_usage_count"
        assert len(metrics.command_usage_count._labelnames) == 3
        assert "group_id" in metrics.command_usage_count._labelnames
        assert "group_name" in metrics.command_usage_count._labelnames
        assert "command_name" in metrics.command_usage_count._labelnames
