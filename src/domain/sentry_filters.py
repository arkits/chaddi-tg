import re

from telegram.error import BadRequest, NetworkError

# PTB's Updater logs every failed getUpdates call and then retries on its own,
# so a dropped connection or a 502 from Telegram is noise, not an incident.
POLLING_LOGGER = "telegram.ext.Updater"

# Telegram puts the bot token in every API URL (api.telegram.org/bot<token>/...),
# and Sentry's httpx integration records those URLs on spans and breadcrumbs
BOT_TOKEN_REGEX = re.compile(r"\d{6,}:[A-Za-z0-9_-]{30,}")
REDACTED = "<redacted>"


def scrub(value):
    """Recursively redact bot tokens from strings, dicts, lists and tuples."""
    if isinstance(value, str):
        return BOT_TOKEN_REGEX.sub(REDACTED, value)
    if isinstance(value, dict):
        return {key: scrub(item) for key, item in value.items()}
    if isinstance(value, list):
        return [scrub(item) for item in value]
    if isinstance(value, tuple):
        return tuple(scrub(item) for item in value)
    return value


def before_send(event: dict, hint: dict) -> dict | None:
    """Drop transient polling network errors and redact tokens from the rest."""
    exc = (hint.get("exc_info") or (None, None, None))[1]

    # BadRequest subclasses NetworkError in PTB, but it means we sent something
    # Telegram rejected - that one is worth seeing
    if (
        event.get("logger") == POLLING_LOGGER
        and isinstance(exc, NetworkError)
        and not isinstance(exc, BadRequest)
    ):
        return None

    return scrub(event)


def before_send_transaction(event: dict, hint: dict) -> dict:
    return scrub(event)


def before_breadcrumb(crumb: dict, hint: dict) -> dict:
    return scrub(crumb)


def before_send_log(log: dict, hint: dict) -> dict:
    return scrub(log)


def scrub_loguru_record(record: dict) -> None:
    """loguru patcher - keeps tokens out of the console, log files and PostHog."""
    record["message"] = scrub(record["message"])
