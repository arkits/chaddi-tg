from unittest.mock import MagicMock, patch


def test_setup_otel_logging_no_api_key():
    """Test setup when PostHog API key is not configured."""
    from src.domain import otel_logging

    original_app_config = otel_logging.app_config

    mock_app_config = MagicMock()
    mock_app_config.get.return_value = "YOUR_POSTHOG_API_KEY"
    otel_logging.app_config = mock_app_config

    with patch("src.domain.otel_logging.logger") as mock_logger:
        otel_logging.setup_otel_logging()
        mock_logger.warning.assert_called_once()

    otel_logging.app_config = original_app_config


def test_setup_otel_logging_with_api_key():
    """Test successful setup with valid API key."""
    from src.domain import otel_logging

    original_app_config = otel_logging.app_config

    mock_app_config = MagicMock()
    mock_app_config.get.return_value = "test_api_key"
    otel_logging.app_config = mock_app_config

    with (
        patch("src.domain.otel_logging.LoggerProvider") as mock_logger_provider,
        patch("src.domain.otel_logging.OTLPLogExporter") as mock_exporter,
        patch("src.domain.otel_logging.get_logger") as mock_get_logger,
        patch("src.domain.otel_logging.logger") as mock_loguru,
        patch("src.domain.otel_logging.set_logger_provider") as mock_set_provider,
    ):
        mock_lp_instance = MagicMock()
        mock_logger_provider.return_value = mock_lp_instance

        mock_exporter_instance = MagicMock()
        mock_exporter.return_value = mock_exporter_instance

        mock_otel_logger = MagicMock()
        mock_get_logger.return_value = mock_otel_logger

        otel_logging.setup_otel_logging()

        mock_set_provider.assert_called_once()
        mock_exporter.assert_called_once()
        mock_lp_instance.add_log_record_processor.assert_called_once()
        mock_loguru.add.assert_called_once()

    otel_logging.app_config = original_app_config


def test_setup_otel_logging_exception():
    """Test setup when an exception occurs."""
    from src.domain import otel_logging

    original_app_config = otel_logging.app_config

    mock_app_config = MagicMock()
    mock_app_config.get.side_effect = Exception("Config error")
    otel_logging.app_config = mock_app_config

    with patch("src.domain.otel_logging.logger") as mock_logger:
        otel_logging.setup_otel_logging()
        mock_logger.error.assert_called_once()

    otel_logging.app_config = original_app_config
