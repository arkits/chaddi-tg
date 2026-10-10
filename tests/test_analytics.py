from unittest.mock import patch

from src.domain import analytics


def test_posthog_disabled_without_api_key():
    # conftest's mock config has no POSTHOG API key
    assert analytics.posthog.disabled is True


def test_capture_exception_forwards_to_posthog():
    error = ValueError("nope")
    with patch.object(analytics.posthog, "capture_exception") as mock_capture:
        analytics.capture_exception(error, distinct_id="42", properties={"a": 1})

    mock_capture.assert_called_once_with(error, distinct_id="42", properties={"a": 1})


def test_capture_exception_ignores_none():
    with patch.object(analytics.posthog, "capture_exception") as mock_capture:
        analytics.capture_exception(None)

    mock_capture.assert_not_called()


def test_capture_exception_never_raises():
    with patch.object(analytics.posthog, "capture_exception", side_effect=RuntimeError("down")):
        analytics.capture_exception(ValueError("nope"))
