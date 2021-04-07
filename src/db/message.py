from telegram import Update
from . import Message
from loguru import logger
import datetime


def log_message_from_update(update: Update):

    logger.debug("[log] Building Message based on update={}", update.to_json())

    Message.create(
        message_id=update.message.message_id,
        time_sent=datetime.datetime.now(),
        from_id=update.message.from_user.id,
        to_id=update.message.chat.id,
        text=update.message.text,
        update=update.to_dict(),
    )

    return
