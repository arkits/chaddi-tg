from telegram.error import BadRequest, NetworkError

# PTB's Updater logs every failed getUpdates call and then retries on its own,
# so a dropped connection or a 502 from Telegram is noise, not an incident.
POLLING_LOGGER = "telegram.ext.Updater"


def before_send(event: dict, hint: dict) -> dict | None:
    """Drop transient polling network errors before they reach Sentry."""
    exc = (hint.get("exc_info") or (None, None, None))[1]

    # BadRequest subclasses NetworkError in PTB, but it means we sent something
    # Telegram rejected - that one is worth seeing
    if (
        event.get("logger") == POLLING_LOGGER
        and isinstance(exc, NetworkError)
        and not isinstance(exc, BadRequest)
    ):
        return None

    return event
