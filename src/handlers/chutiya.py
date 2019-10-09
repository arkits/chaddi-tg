#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ChaddiBot
https://ghati.bitbucket.io/
"""

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import util
import config
import bakchod_util

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Handler /chutiya
def handle(bot, update):

    bakchod_util.bakchod_updater(update.message.from_user['username'])

    logger.info("/chutiya: Handling /chutiya request from user '%s' in group '%s'", update.message.from_user['username'], update.message.chat.title)

    if(update.message.reply_to_message):
        og_from = update.message.reply_to_message.from_user
    else:
        og_from = update.message.from_user

    if(og_from.username):
        og_sender = og_from['username']
    elif(og_from.first_name):
        og_sender = og_from['firstname']
    else:
        og_sender = "A Bakchod"

    if og_sender != config.bot_username:
        update.message.reply_to_message.reply_text(og_sender + " is a c♥h♥u♥t♥i♥y♥a♥")
    else:
        sticker_to_send = 'CAADAQADrAEAAp6M4Ahtgp9JaiLJPxYE'
        update.message.reply_sticker(sticker=sticker_to_send)