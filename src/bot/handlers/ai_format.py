"""Formatting Telegram messages as lines of chat transcript for the /ai prompt."""

import contextlib
from datetime import datetime

from src.domain import util

# How the bot's own messages are labelled in the transcript
BOT_NAME = "Chaddi (you)"

# Long messages are cut down in the transcript to keep it compact
MAX_TEXT_LENGTH = 500
# Quoted parts of replied-to messages are cut down to this
MAX_QUOTE_LENGTH = 200


def format_time(value) -> str | None:
    """Format a time in the server's timezone, eg. `Thu Sep 24 18:05`."""
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is not None:
        value = value.astimezone()
    return value.strftime("%a %b %d %H:%M")


def to_local_naive(value) -> datetime | None:
    """Convert a Telegram (UTC) time to the naive local time messages are logged with."""
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is not None:
        value = value.astimezone().replace(tzinfo=None)
    return value


def format_header(message_id, time) -> str:
    message_ref = f"#{message_id}" if message_id is not None else None
    parts = [p for p in (message_ref, format_time(time)) if p]
    return f"[{' '.join(parts)}]" if parts else ""


def format_line(
    message_id=None,
    time=None,
    name: str = "",
    reply_to_id=None,
    text: str | None = None,
    media: str | None = None,
    quote: str | None = None,
) -> str:
    """Format a message as `[#id time] name (replying to #id, quoting "…"): [media] text`."""
    line = " ".join(p for p in (format_header(message_id, time), name) if p)
    if reply_to_id is not None:
        reply = f"replying to #{reply_to_id}"
        if quote:
            reply += f', quoting "{truncate(quote, MAX_QUOTE_LENGTH)}"'
        line += f" ({reply})"
    body = " ".join(p for p in (media, text) if p) or "(no text)"
    return f"{line}: {body}"


def truncate(text: str, limit: int) -> str:
    return text[:limit] + "…" if len(text) > limit else text


def message_dict(message) -> dict:
    """A live Telegram message as a dict, the same shape as logged updates."""
    with contextlib.suppress(Exception):
        data = message.to_dict()
        if isinstance(data, dict):
            return data
    return {}


def stored_message(message) -> dict:
    """The Telegram message dict saved with a logged Message row."""
    update = message.update if isinstance(message.update, dict) else {}
    stored = update.get("message")
    return stored if isinstance(stored, dict) else {}


def live_quote(message) -> str | None:
    """The part of the replied-to message a live message quotes, if any."""
    quote = getattr(message, "quote", None)
    text = getattr(quote, "text", None)
    return text if isinstance(text, str) and text else None


def media_group_id(message) -> str | None:
    """The album a live message belongs to, if any."""
    value = getattr(message, "media_group_id", None)
    return value if isinstance(value, str) and value else None


def media_label(message: dict) -> str | None:
    """Describe what media a message (as a dict) carries, eg. `[photo]`."""
    if not isinstance(message, dict):
        return None

    # Animations also set `document`, so check them first
    if message.get("animation") is not None:
        return "[GIF]"
    sticker = message.get("sticker")
    if isinstance(sticker, dict):
        emoji = sticker.get("emoji")
        return f"[sticker {emoji}]" if emoji else "[sticker]"
    document = message.get("document")
    if isinstance(document, dict):
        name = document.get("file_name")
        return f"[file: {name}]" if name else "[file]"
    poll = message.get("poll")
    if isinstance(poll, dict):
        return f"[poll: {poll.get('question', '')}]"

    for key, label in (
        ("photo", "photo"),
        ("video", "video"),
        ("video_note", "video message"),
        ("voice", "voice message"),
        ("audio", "audio"),
        ("location", "location"),
        ("contact", "contact"),
    ):
        if message.get(key) is not None:
            return f"[{label}]"
    return None


def reply_to_message_id(message: dict) -> int | None:
    """The replied-to message id from a message dict."""
    reply_to = message.get("reply_to_message") if isinstance(message, dict) else None
    if not isinstance(reply_to, dict):
        return None
    return reply_to.get("message_id")


def stored_quote(message: dict) -> str | None:
    quote = message.get("quote") if isinstance(message, dict) else None
    if not isinstance(quote, dict):
        return None
    text = quote.get("text")
    return text if isinstance(text, str) and text else None


def format_chat_message(message, max_text_length: int = MAX_TEXT_LENGTH) -> str:
    """Format a logged Message as a line of chat history."""
    stored = stored_message(message)
    text = message.text or stored.get("caption") or ""
    return format_line(
        message_id=message.message_id,
        time=message.time_sent,
        name=util.extract_pretty_name_from_bakchod(message.from_bakchod),
        reply_to_id=reply_to_message_id(stored),
        text=truncate(text, max_text_length),
        media=media_label(stored),
        quote=stored_quote(stored),
    )
