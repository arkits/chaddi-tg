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
) -> list[Message]:
    """
    Fetch logged text messages from a chat, oldest first.

    Args:
        chat_id: The chat to read from.
        limit: Maximum number of messages to return.
        before_message_id: Only return messages sent before this Telegram message id.
        search: Only return messages whose text contains this (case-insensitive).

    Returns:
        Up to `limit` of the most recent matching messages, in chronological order.
    """
    query = (
        Message.select(Message, Bakchod)
        .join(Bakchod)
        .where(Message.to_id == str(chat_id))
        .where(Message.text.is_null(False))
    )

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

    messages = list(query.order_by(Message.time_sent.desc()).limit(limit))
    messages.reverse()
    return messages
