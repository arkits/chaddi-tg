import datetime

from loguru import logger
from telegram import Update

from src.domain import metrics, util

from . import Bakchod, Message


def log_message_from_update(update: Update):
    # logger.debug("[log] Building Message based on update={}", update.to_json())

    from_bakchod = Bakchod.get_by_id(update.message.from_user.id)

    m = Message.create(
        message_id=update.message.message_id,
        time_sent=datetime.datetime.now(),
        from_bakchod=from_bakchod,
        to_id=update.message.chat.id,
        text=update.message.text,
        update=update.to_dict(),
    )

    logger.trace(
        "[db] saved Message - id={} from={}",
        m.message_id,
        util.extract_pretty_name_from_bakchod(from_bakchod),
    )

    metrics.inc_message_count(update)

    return m


def get_chat_messages(
    chat_id: str | int,
    limit: int = 30,
    before_message_id: str | int | None = None,
    search: str | None = None,
    since: datetime.datetime | None = None,
) -> list[Message]:
    """
    Fetch logged messages from a chat, oldest first.

    Media messages (photos, files, stickers...) have no text, but are still
    returned - their stored update says what was sent.

    Args:
        chat_id: The chat to read from.
        limit: Maximum number of messages to return.
        before_message_id: Only return messages sent before this Telegram message id.
        search: Only return messages whose text contains this (case-insensitive).
        since: Only return messages sent after this time.

    Returns:
        Up to `limit` of the most recent matching messages, in chronological order.
    """
    query = Message.select(Message, Bakchod).join(Bakchod).where(Message.to_id == str(chat_id))

    if before_message_id is not None:
        anchor = (
            Message.select(Message.time_sent)
            .where(Message.to_id == str(chat_id))
            .where(Message.message_id == str(before_message_id))
            .first()
        )
        if anchor is not None:
            query = query.where(Message.time_sent < anchor.time_sent)

    if search:
        query = query.where(Message.text.contains(search))

    if since is not None:
        query = query.where(Message.time_sent > since)

    messages = list(query.order_by(Message.time_sent.desc()).limit(limit))
    messages.reverse()
    return messages


def get_message(chat_id: str | int, message_id: str | int) -> Message | None:
    """Fetch one logged message from a chat by its Telegram message id."""
    return (
        Message.select(Message, Bakchod)
        .join(Bakchod)
        .where(Message.to_id == str(chat_id))
        .where(Message.message_id == str(message_id))
        .first()
    )


def get_messages_between(
    chat_id: str | int,
    start: datetime.datetime,
    end: datetime.datetime,
    limit: int = 50,
) -> list[Message]:
    """Fetch logged messages from a chat sent between two times, oldest first."""
    return list(
        Message.select(Message, Bakchod)
        .join(Bakchod)
        .where(Message.to_id == str(chat_id))
        .where(Message.time_sent >= start)
        .where(Message.time_sent <= end)
        .order_by(Message.time_sent)
        .limit(limit)
    )
