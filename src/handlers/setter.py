#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import random
import bakchod_util
import dateparser
from telegram import ParseMode
import config

# Enable logging
logger = logging.getLogger(__name__)

# Setter Handler
def handle(bot, update):
    logger.info("/set: Handling /set request")

    message = update.message.text
    message = message.split(' ')
    logger.info(message)

    if update.message.reply_to_message:
        for_bakchod = update.message.reply_to_message.from_user['id']
    else:
        for_bakchod = update.message.from_user['id']
    
    og_bakchod = update.message.from_user['id']

    response = parse_request(message, for_bakchod, og_bakchod)
    
    update.message.reply_text(
        text=response, 
        parse_mode=ParseMode.MARKDOWN
    )

def parse_request(request, for_bakchod, og_bakchod):

    try:
        set_type = request[1]
    except IndexError:
        response = "❔ Please include what you want to set"
        return response

    if set_type.lower() == "birthday":

        try:
            birthday = request[2]
        except IndexError:
            response = "Please include your birthday - `/set birthday 4/20/1969`"
            return response

        if can_set(for_bakchod, og_bakchod):
            bday_reponse = set_bakchod_birthday(birthday, for_bakchod)
            response = bday_reponse
        else:
            response = "❌ Can't set that." 
        
    else:

        response = "❌ Can't set that." 

    logger.info(response)
    return response

def set_bakchod_birthday(birthday, bakchod_id):

    bakchod = bakchod_util.get_bakchod(bakchod_id)

    birthday = dateparser.parse(birthday)

    bakchod.birthday = birthday

    bakchod_util.set_bakchod(bakchod)

    reponse = "✅ Set {}'s Birthday to {} {} {}!".format(
        bakchod.username, 
        bakchod.birthday.day,
        bakchod.birthday.strftime('%b'),
        bakchod.birthday.year,
    )

    return reponse


def can_set(for_bakchod, og_bakchod):
    if og_bakchod == for_bakchod:
        logger.info("can_set: og_bakchod == for_bakchod")
        return True
    elif og_bakchod in config.allowed_setters:
        logger.info("can_set: og_bakchod in config.allowed_setters")
        return True
    else:
        return False