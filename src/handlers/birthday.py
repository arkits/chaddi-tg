#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode

import logging
import random
from datetime import datetime
from util import bakchod_util
import config

# Enable logging
logger = logging.getLogger(__name__)


# Handler /birthday
def handle(bot, update):

    logger.info("/birthday: Handling /birthday request from user '%s' in group '%s'", update.message.from_user['username'], update.message.chat.title)

    reponse = generate_birthday_response()

    update.message.reply_text(reponse)

def daily_job(bot, job):
    logger.info('birthday.daily_job: Running birthday.daily_job')
    bot.send_message(chat_id=config.mains_chat_id, text=generate_birthday_response())


def generate_birthday_response():

    bakchod_dict = bakchod_util.bakchod_dict

    response = ""

    birthday_bakchods = []

    today = datetime.now()

    for bakchod_id in bakchod_util.bakchod_dict:

        bakchod = bakchod_dict[bakchod_id]

        try:
            bakchod_birthday = bakchod.birthday
            
            if bakchod_birthday.day == today.day and bakchod_birthday.month == today.month:
                birthday_bakchods.append(bakchod)
        
        except:
            logger.debug("/birthday: Birthday wasn't set for %s ", bakchod.username)

    if len(birthday_bakchods) == 0:
        response = "Looks like it's no ones birthday today :("
    else:
        response = "🎂 HAPPY BIRTHDAY 🎂 \n"
        
        for bakchod in birthday_bakchods:
            response = response + "🎉 " + bakchod.username + "\n"

    return(response)
