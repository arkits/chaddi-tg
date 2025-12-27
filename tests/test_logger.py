import logging

import pytest

from src.domain.logger import InterceptHandler, intercept_logs_with_loguru


class TestInterceptHandler:
    def test_handler_emits_info_message(self, caplog):
        """Test that InterceptHandler emits INFO messages correctly"""
        handler = InterceptHandler()

        with caplog.at_level(logging.INFO):
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg="Test message",
                args=(),
                exc_info=None,
            )
            handler.emit(record)

        assert len(caplog.records) == 0

    def test_handler_handles_unknown_level(self):
        """Test that handler handles unknown log levels gracefully"""
        handler = InterceptHandler()

        record = logging.LogRecord(
            name="test",
            level=logging.NOTSET,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Should not raise exception
        try:
            handler.emit(record)
        except Exception as e:
            pytest.fail(f"Handler raised exception for unknown level: {e}")

    def test_handler_with_exception(self):
        """Test that handler handles exception records correctly"""
        handler = InterceptHandler()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error message",
            args=(),
            exc_info=(Exception, Exception("Test exception"), None),
        )

        # Should not raise exception
        try:
            handler.emit(record)
        except Exception as e:
            pytest.fail(f"Handler raised exception with exc_info: {e}")

    def test_intercept_logs_with_loguru(self):
        """Test that intercept_logs_with_loguru configures logging without errors"""
        # This should not raise any exceptions
        intercept_logs_with_loguru()

        # Verify logging is configured
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0
