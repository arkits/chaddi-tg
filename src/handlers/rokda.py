from loguru import logger
from util import util, dao


def handle(update, context):

    util.log_chat("rokda", update)

    if update.message.reply_to_message:
        bakchod_id = update.message.reply_to_message.from_user["id"]
    else:
        bakchod_id = update.message.from_user["id"]

    bakchod = dao.get_bakchod(bakchod_id)

    if bakchod is not None:

        response = "💰" + bakchod.username + " has " + str(bakchod.rokda) + " ₹okda!"
        logger.info("[rokda] Sending response " + response)
        update.message.reply_text(response)

    else:

        logger.info("[rokda] Couldn't find user")
        file_id = "CAADAwADrQADnozgCI_qxocBgD_OFgQ"
        sticker_to_send = file_id
        update.message.reply_sticker(sticker=sticker_to_send)
