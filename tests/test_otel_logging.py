from unittest.mock import MagicMock, patch


def test_setup_otel_logging_no_api_key():
    """Test setup when PostHog API key is not configured."""
    with patch("src.domain.otel_logging.logger") as mock_logger:
        with patch("src.domain.otel_logging.config") as mock_config:
            mock_app_config = MagicMock()
            mock_app_config.get.return_value = "YOUR_POSTHOG_API_KEY"
            mock_config.get_config.return_value = mock_app_config

            from src.domain.otel_logging import setup_otel_logging

            setup_otel_logging()

            mock_logger.warning.assert_called_once()


def test_setup_otel_logging_with_api_key():
    """Test successful setup with valid API key."""
    with patch("src.domain.otel_logging.logger") as mock_logger:
        with patch("src.domain.otel_logging.config") as mock_config:
            with patch("src.domain.otel_logging.set_logger_provider") as mock_set_provider:
                with patch("src.domain.otel_logging.LoggerProvider") as mock_logger_provider:
                    with patch("src.domain.otel_logging.OTLPLogExporter") as mock_exporter:
                        with patch("src.domain.otel_logging.get_logger") as mock_get_logger:
                            with patch("src.domain.otel_logging.logger") as mock_loguru:
                                mock_app_config = MagicMock()
                                mock_app_config.get.return_value = "test_api_key"
                                mock_config.get_config.return_value = mock_app_config

                                mock_lp_instance = MagicMock()
                                mock_logger_provider.return_value = mock_lp_instance

                                mock_exporter_instance = MagicMock()
                                mock_exporter.return_value = mock_exporter_instance

                                mock_otel_logger = MagicMock()
                                mock_get_logger.return_value = mock_otel_logger

                                from src.domain.otel_logging import setup_otel_logging

                                setup_otel_logging()

                                mock_set_provider.assert_called_once()
                                mock_exporter.assert_called_once()
                                mock_lp_instance.add_log_record_processor.assert_called_once()
                                mock_loguru.add.assert_called_once()


def test_setup_otel_logging_exception():
    """Test setup when an exception occurs."""
    with patch("src.domain.otel_logging.logger") as mock_logger:
        with patch("src.domain.otel_logging.config") as mock_config:
            mock_app_config = MagicMock()
            mock_app_config.get.side_effect = Exception("Config error")
            mock_config.get_config.return_value = mock_app_config

            from src.domain.otel_logging import setup_otel_logging

            setup_otel_logging()

            mock_logger.error.assert_called_once()
