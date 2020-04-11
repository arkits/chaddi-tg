from loguru import logger
from util import util
from db import dao
from telegram import ParseMode


def handle(update, context):

    util.log_chat("set", update)

    message = update.message.text
    message = message.split(" ")

    if update.message.reply_to_message:
        for_bakchod = update.message.reply_to_message.from_user["id"]
    else:
        for_bakchod = update.message.from_user["id"]

    og_bakchod = update.message.from_user["id"]

    response = parse_request(message, for_bakchod, og_bakchod, update)

    update.message.reply_text(text=response, parse_mode=ParseMode.MARKDOWN)


def parse_request(request, for_bakchod, og_bakchod, tg_update):

    try:
        set_type = request[1]
    except IndexError:
        response = "❔ Please include what you want to set"
        return response

    if set_type.lower() == "rokda":

        try:
            rokda_to_set = float(request[2])
        except IndexError:
            response = "Please include rokda to set - `/set rokda 1337`"
            return response

        if util.is_admin(og_bakchod):
            set_reponse = set_bakchod_rokda(rokda_to_set, for_bakchod)
            response = set_reponse
        else:
            response = "❌ Not allowed to set rokda."

    else:

        response = "❌ Can't set that."

    logger.info(response)
    return response


def set_bakchod_rokda(rokda_to_set, bakchod_id):

    bakchod = dao.get_bakchod_by_id(bakchod_id)

    bakchod.rokda = rokda_to_set

    dao.insert_bakchod(bakchod)

    reponse = "✅ Set {}'s ₹okda to {}!".format(bakchod.username, bakchod.rokda)

    return reponse
