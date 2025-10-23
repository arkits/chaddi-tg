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
