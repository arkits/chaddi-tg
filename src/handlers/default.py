#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode

import util
import handlers.hi as hi_handler
import bakchod_util

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Handle /start
def start(bot, update):
    # Updated timesince
    bakchod_util.bakchod_updater(update.message.from_user['username'])

    logger.info('/start: Handling /start response')
    logger.info("Request from user '%s' in group '%s'", update.message.from_user['username'], update.message.chat.title)
    update.message.reply_text(util.random_reply())

# Handle erros
def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)

# Handle all text messages received
def all_text(bot, update):

    # logger.info("all_text: Received text message from user '%s' in group '%s'", update.message.from_user['username'], update.message.chat.title)

    message_text = update.message.text

    bakchod_util.bakchod_updater(update.message.from_user['username'])

    # TODO: Handle this through custom filters
    if(message_text == 'hi' or message_text == 'Hi'):
        hi_handler.handle(bot, update)

# Handle all text messages received
def all_sticker(bot, update):

    # logger.info("all_sticker: Received Sticker Message from user '%s' in group '%s'", update.message.from_user['username'], update.message.chat.title)
    
    bakchod_util.bakchod_updater(update.message.from_user['username'])
