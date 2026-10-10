from telegram.error import BadRequest, Conflict, NetworkError, TimedOut

from src.domain import sentry_filters


def hint_for(exc: Exception) -> dict:
    return {"exc_info": (type(exc), exc, None)}


def test_drops_polling_network_errors():
    event = {"logger": "telegram.ext.Updater"}

    assert sentry_filters.before_send(event, hint_for(NetworkError("httpx.ReadError: "))) is None
    assert sentry_filters.before_send(event, hint_for(NetworkError("Bad Gateway"))) is None
    assert sentry_filters.before_send(event, hint_for(TimedOut())) is None


def test_keeps_polling_conflicts():
    # Two bot instances fighting over getUpdates is a real problem worth hearing about
    event = {"logger": "telegram.ext.Updater"}

    assert sentry_filters.before_send(event, hint_for(Conflict("terminated"))) is event


def test_keeps_network_errors_from_other_loggers():
    event = {"logger": "src.bot.handlers.x_links"}

    assert sentry_filters.before_send(event, hint_for(NetworkError("boom"))) is event


def test_keeps_events_without_an_exception():
    event = {"logger": "telegram.ext.Updater", "message": "something"}

    assert sentry_filters.before_send(event, {}) is event


def test_keeps_other_telegram_errors():
    event = {"logger": "telegram.ext.Updater"}

    assert sentry_filters.before_send(event, hint_for(BadRequest("nope"))) is event
