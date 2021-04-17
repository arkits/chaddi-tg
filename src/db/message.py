from telegram import Update
from . import Bakchod, Message
from loguru import logger
import datetime


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

    logger.debug(
        "[db] saved Message - id={} from={}", m.message_id, from_bakchod.username
    )

    return
