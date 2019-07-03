#!/usr/bin/env python
# -*- coding: utf-8 -*-

###################################################################
#                         ChaddiBot                               #
#                        Archit Khode                             #
###################################################################


from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
import logging
import random
from datetime import datetime
import config
import util

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def start(bot, update):
    # Updated timesince
    util.timesince_updater(update.message.from_user['username'])

    # Handle /start
    logger.info('/start: Handling /start response')
    update.message.reply_text(util.random_reply())

def error(bot, update, error):
    # Handle erros
    logger.warning('Update "%s" caused error "%s"', update, error)

def hi(bot, update):

    hi_response_whitelist = ["pahagwl", "arkits"]

    if(update.message.from_user['username'] in hi_response_whitelist):
        logger.info('/hi: Handling /hi message')
        update.message.reply_text(util.random_reply())

def all_text(bot, update):
    # Handle all text messages received
    # logger.info('Received Text Message:')
    # logger.info(update.message)
    # logger.info(' ')

    message_text = update.message.text

    util.timesince_updater(update.message.from_user['username'])

    # util.chat_export(update.message)
    
    # TODO: Handle this through custom filters
    if(message_text == 'hi' or message_text == 'Hi'):
        logger.info('all_text: Detected Hi msg')
        hi(bot, update)

def all_sticker(bot, update):
    # Handle all text messages received
    logger.info('all_sticker: Received Sticker Message:')
    util.timesince_updater(update.message.from_user['username'])
    logger.info(update.message)

def superpower(bot, update):
    # Handle /timesince
    logger.info('/superpower: Handling /superpower input')
    response = "🇮🇳🙏 Time Until Super Power™️: " + util.superpower_countdown_calc() + " 🙏🇮🇳"
    update.message.reply_text(response)

def timesince(bot, update):
    # Handle /timesince
    logger.info('/timesince: Handling /timesince input')

    query_username = update.message.text
    query_username = query_username[11:]

    if len(query_username) == 0:
        logger.info('/timesince: Input format was wrong.')
        update.message.reply_text("Reply with a username - /timesince @arkits")
    else:
        logger.info("/timesince: Query for: " + query_username)
        response = util.timesince_query(query_username)

        if response == "404":
            logger.info("/timesince: Couldn't find user")
            file_id = 'CAADAQADfAEAAp6M4Ah03h6oF-p4GwI'
            sticker_to_send = file_id
            update.message.reply_sticker(sticker=sticker_to_send)
        else:
            logger.info("/timesince: Sending response " + response)
            update.message.reply_text(response)
    
    # Updating timesince
    util.timesince_updater(update.message.from_user['username'])