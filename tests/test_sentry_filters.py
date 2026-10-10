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

    assert sentry_filters.before_send(event, hint_for(Conflict("terminated"))) == event


def test_keeps_network_errors_from_other_loggers():
    event = {"logger": "src.bot.handlers.x_links"}

    assert sentry_filters.before_send(event, hint_for(NetworkError("boom"))) == event


def test_keeps_events_without_an_exception():
    event = {"logger": "telegram.ext.Updater", "message": "something"}

    assert sentry_filters.before_send(event, {}) == event


def test_keeps_other_telegram_errors():
    event = {"logger": "telegram.ext.Updater"}

    assert sentry_filters.before_send(event, hint_for(BadRequest("nope"))) == event


TOKEN = "123456789:AAFakeTokenFakeTokenFakeTokenFake12"
URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"


def test_scrub_redacts_tokens_in_nested_structures():
    event = {
        "contexts": {"trace": {"description": f"POST {URL}"}},
        "spans": [{"description": f"POST {URL}", "data": {"url": URL}}],
        "tags": ("ok", URL),
        "count": 3,
    }

    scrubbed = sentry_filters.scrub(event)

    assert TOKEN not in repr(scrubbed)
    assert scrubbed["spans"][0]["data"]["url"] == (
        "https://api.telegram.org/bot<redacted>/sendMessage"
    )
    assert scrubbed["count"] == 3


def test_scrub_leaves_ordinary_text_alone():
    text = "message_id=24530 chat=-1002005674227 at 13:36:25"

    assert sentry_filters.scrub(text) == text


def test_before_send_scrubs_kept_events():
    event = {"logger": "src.bot", "message": f"failed calling {URL}"}

    assert TOKEN not in sentry_filters.before_send(event, {})["message"]


def test_hooks_scrub_transactions_breadcrumbs_and_logs():
    assert TOKEN not in repr(
        sentry_filters.before_send_transaction({"spans": [{"description": URL}]}, {})
    )
    assert TOKEN not in repr(sentry_filters.before_breadcrumb({"data": {"url": URL}}, {}))
    assert TOKEN not in repr(sentry_filters.before_send_log({"body": URL}, {}))


def test_scrub_loguru_record():
    record = {"message": f"calling {URL}"}

    sentry_filters.scrub_loguru_record(record)

    assert TOKEN not in record["message"]
