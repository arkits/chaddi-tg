"""Analytics and telemetry initialization."""

import contextlib

from posthog import Posthog

from . import config

app_config = config.get_config()

POSTHOG_HOST = "https://us.i.posthog.com"

_api_key = app_config.get("POSTHOG", "API_KEY", fallback="")
_enabled = bool(_api_key) and _api_key != "YOUR_POSTHOG_API_KEY"

posthog = Posthog(
    project_api_key=_api_key or "disabled",
    host=POSTHOG_HOST,
    disabled=not _enabled,
    enable_exception_autocapture=True,
    capture_exception_code_variables=True,
    # Mark our own frames as in-app so stack traces in Error Tracking are grouped by them
    in_app_modules=["src"],
    super_properties={
        "environment": app_config.get("SENTRY", "ENVIRONMENT", fallback="dev"),
    },
)


def capture_exception(
    error: BaseException | None,
    distinct_id: str | None = None,
    properties: dict | None = None,
):
    """Send a handled exception to PostHog Error Tracking. Never raises."""
    if error is None:
        return
    with contextlib.suppress(Exception):
        posthog.capture_exception(error, distinct_id=distinct_id, properties=properties)
