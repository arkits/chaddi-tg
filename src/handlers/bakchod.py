#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ChaddiBot
https://ghati.bitbucket.io/
"""
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode

import util
import bakchod_util

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Handle /timesince
def timesince(bot, update):
    
    logger.info("/timesince: Handling /timesince request from user '%s' in group '%s'", update.message.from_user['username'], update.message.chat.title)

    query_username = update.message.from_user['username']

    if len(query_username) == 0:
        logger.info('/timesince: Input format was wrong.')
        update.message.reply_text("Reply with a username - /timesince @arkits")
    else:
        response = bakchod_util.timesince_query(query_username)

        if response == "404":
            logger.info("/timesince: Couldn't find user")
            file_id = 'CAADAQADfAEAAp6M4Ah03h6oF-p4GwI'
            sticker_to_send = file_id
            update.message.reply_sticker(sticker=sticker_to_send)
        else:
            logger.info("/timesince: Sending response " + response)
            update.message.reply_text(response)
    
    # Updating Bakchod Pickle
    bakchod_util.bakchod_updater(update.message.from_user['username'])

# Handle /timesince
def lakshmi(bot, update):

    if(update.message.reply_to_message):
        query_username = update.message.reply_to_message.from_user['username']
        response = bakchod_util.lakshmi_query(query_username)
    else:
        query_username = update.message.from_user['username']
        response = bakchod_util.lakshmi_query(query_username)

    logger.info("/lakshmi: Handling /lakshmi request from user '%s' initiated by '%s' in group '%s'", update.message.from_user['username'], query_username, update.message.chat.title)

    if response == "404":
        logger.info("/lakshmi: Couldn't find user")
        file_id = 'CAADAwADrQADnozgCI_qxocBgD_OFgQ'
        sticker_to_send = file_id
        update.message.reply_sticker(sticker=sticker_to_send)
    else:
        logger.info("/lakshmi: Sending response " + response)
        update.message.reply_text(response)

    # Updating Bakchod Pickle
    bakchod_util.bakchod_updater(update.message.from_user['username'])