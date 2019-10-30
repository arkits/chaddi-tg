#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import random
import bakchod_util
import dateparser
from telegram import ParseMode
import config
import handlers.macro as macro_handler

# Enable logging
logger = logging.getLogger(__name__)

# Setter Handler
def handle(bot, update):
    logger.info("/set: Handling /set request")

    message = update.message.text
    message = message.split(' ')

    if update.message.reply_to_message:
        for_bakchod = update.message.reply_to_message.from_user['id']
    else:
        for_bakchod = update.message.from_user['id']

    og_bakchod = update.message.from_user['id']

    response = parse_request(message, for_bakchod, og_bakchod, update)

    update.message.reply_text(
        text=response,
        parse_mode=ParseMode.MARKDOWN
    )


def parse_request(request, for_bakchod, og_bakchod, tg_update):

    try:
        set_type = request[1]
    except IndexError:
        response = "❔ Please include what you want to set"
        return response

    if set_type.lower() == "birthday":

        try:
            birthday = ''.join(request[2:])
            birthday = dateparser.parse(birthday)
            if birthday is None:
                raise ValueError
        except:
            response = "Please include your birthday - `/set birthday 4/20/1969`"
            return response

        if can_set(for_bakchod, og_bakchod):
            bday_reponse = set_bakchod_birthday(birthday, for_bakchod)
            response = bday_reponse
        else:
            response = "❌ Not allowed to set birthday."

    elif set_type.lower() == "rokda":

        try:
            rokda_to_set = int(request[2])
        except IndexError:
            response = "Please include rokda to set - `/set rokda 1337`"
            return response

        if is_admin(og_bakchod):
            set_reponse = set_bakchod_rokda(rokda_to_set, for_bakchod)
            response = set_reponse
        else:
            response = "❌ Not allowed to set rokda."

    elif set_type.lower() == "macro":

        try:
            macro_key = request[2]
        except IndexError:
            response = "Please include macro command to set - `/set macro command`"
            return response

        if is_admin(og_bakchod):
            set_reponse = set_macro(macro_key, tg_update)
            response = set_reponse
        else:
            response = "❌ Not allowed to set macro."

    else:

        response = "❌ Can't set that."

    logger.info(response)
    return response


def set_bakchod_birthday(birthday, bakchod_id):

    bakchod = bakchod_util.get_bakchod(bakchod_id)

    bakchod.birthday = birthday

    bakchod_util.set_bakchod(bakchod)

    reponse = "✅ Set {}'s Birthday to {} {} {}!".format(
        bakchod.username,
        bakchod.birthday.day,
        bakchod.birthday.strftime('%b'),
        bakchod.birthday.year,
    )

    return reponse


def set_bakchod_rokda(rokda_to_set, bakchod_id):

    bakchod = bakchod_util.get_bakchod(bakchod_id)

    bakchod.rokda = rokda_to_set

    bakchod_util.set_bakchod(bakchod)

    reponse = "✅ Set {}'s ₹okda to {}!".format(
        bakchod.username,
        bakchod.rokda
    )

    return reponse


def set_macro(macro_key, tg_update):

    macro_to_set = {}

    macro_key = '/' + macro_key

    sticker = tg_update.message.reply_to_message.sticker

    if sticker is not None:
        macro_to_set['is_sticker'] = True
        macro_to_set['data'] = sticker.file_id
    else:
        macro_to_set['is_sticker'] = False
        macro_to_set['data'] = tg_update.message.reply_to_message.text

    logger.info("Parsed Macro - %s", macro_to_set)

    macro_handler.add_to_macros(macro_key, macro_to_set)

    response = "✅ Set Macro - {}".format(macro_key)

    return response


def can_set(for_bakchod, og_bakchod):
    if og_bakchod == for_bakchod:
        logger.info("can_set: og_bakchod == for_bakchod")
        return True
    elif str(og_bakchod) in config.allowed_setters:
        logger.info("can_set: og_bakchod in config.allowed_setters")
        return True
    else:
        return False


def is_admin(og_bakchod):
    if str(og_bakchod) in config.allowed_setters:
        logger.info("is_admin: og_bakchod in config.allowed_setters")
        return True
    else:
        return False
