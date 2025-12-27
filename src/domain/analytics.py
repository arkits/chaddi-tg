"""Analytics and telemetry initialization."""

from posthog import Posthog

from . import config

app_config = config.get_config()

posthog = Posthog(
    project_api_key=app_config.get("POSTHOG", "API_KEY"),
    host="https://us.i.posthog.com",
    enable_exception_autocapture=True,
    capture_exception_code_variables=True,
)
