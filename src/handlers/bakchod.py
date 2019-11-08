#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode

import logging
from util import bakchod_util

# Enable logging
logger = logging.getLogger(__name__)


# Handle /timesince
def timesince(bot, update):
    
    if update.message.reply_to_message:
        query_username = "@" + update.message.reply_to_message.from_user['username']
    else:
        query_username = update.message.text[11:]

    logger.info("/timesince: Handling /timesince request from user '%s' for '%s' in group '%s'", update.message.from_user['username'], query_username, update.message.chat.title)

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


# Handle /rokda
def rokda(bot, update):

    if(update.message.reply_to_message):
        query_id = update.message.reply_to_message.from_user['id']
        response = bakchod_util.rokda_query(query_id)
    else:
        query_id = update.message.from_user['id']
        response = bakchod_util.rokda_query(query_id)

    logger.info("/rokda: Handling /rokda request from user '%s' for '%s' in group '%s'", update.message.from_user['username'], query_id, update.message.chat.title)

    if response == "404":
        logger.info("/rokda: Couldn't find user")
        file_id = 'CAADAwADrQADnozgCI_qxocBgD_OFgQ'
        sticker_to_send = file_id
        update.message.reply_sticker(sticker=sticker_to_send)
    else:
        logger.info("/rokda: Sending response " + response)
        update.message.reply_text(response)

# Handle /about
def about(bot, update):

    if(update.message.reply_to_message):
        query_id = update.message.reply_to_message.from_user['id']
        response = bakchod_util.about_query(query_id)
    else:
        query_id = update.message.from_user['id']
        response = bakchod_util.about_query(query_id)

    logger.info("/about: Handling /about request from user '%s' for '%s' in group '%s'", update.message.from_user['username'], query_id, update.message.chat.title)

    if response == "404":
        logger.info("/about: Couldn't find user")
        file_id = 'CAADAwADrQADnozgCI_qxocBgD_OFgQ'
        sticker_to_send = file_id
        update.message.reply_sticker(sticker=sticker_to_send)
    else:
        logger.info("/about: Sending response " + response)

        update.message.reply_text(
            text=response, 
            parse_mode=ParseMode.MARKDOWN
        )

