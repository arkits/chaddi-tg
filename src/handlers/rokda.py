from loguru import logger
from util import util
from db import dao


def handle(update, context):

    util.log_chat("rokda", update)

    if update.message.reply_to_message:
        bakchod_id = update.message.reply_to_message.from_user["id"]
    else:
        bakchod_id = update.message.from_user["id"]

    bakchod = dao.get_bakchod_by_id(bakchod_id)

    if bakchod is not None:

        response = "💰" + util.extract_pretty_name_from_bakchod(bakchod) + " has " + str(round(bakchod.rokda, 2)) + " ₹okda!"
        logger.info("[rokda] Sending response " + response)
        update.message.reply_text(response)

    else:

        logger.info("[rokda] Couldn't find user")
        file_id = "CAADAwADrQADnozgCI_qxocBgD_OFgQ"
        sticker_to_send = file_id
        update.message.reply_sticker(sticker=sticker_to_send)
