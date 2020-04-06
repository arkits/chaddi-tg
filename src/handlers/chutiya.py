from loguru import logger
from util import util, extract_pretty_name
import random
from telegram import ParseMode


def handle(update, context):

    util.log_chat("chutiya", update)

    response = None

    try:
        logger.info("[chutiya]: from user {} in group {}", update.message.from_user['username'], update.message.chat.title)

        if(update.message.reply_to_message):
            og_from = update.message.reply_to_message.from_user
        else:
            og_from = update.message.from_user

        og_sender = extract_pretty_name(og_from)

        if og_sender != config.bot_username:
            update.message.reply_to_message.reply_text(og_sender + " is a \nc♥h♥u♥t♥i♥y♥a♥")
        else:
            sticker_to_send = 'CAADAQADrAEAAp6M4Ahtgp9JaiLJPxYE'
            update.message.reply_sticker(sticker=sticker_to_send)
    except Exception as e:
        logger.error(
            "[chutiya] Caught Error! e={} \n update.message={} ", e, update.message
        )
        response = "bhak bc"

    update.message.reply_text(text=response, parse_mode=ParseMode.MARKDOWN)