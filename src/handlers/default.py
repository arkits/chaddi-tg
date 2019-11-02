#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode

import util
import handlers.hi as hi_handler
import handlers.bestie as bestie_handler
import handlers.macro as macro_handler
import bakchod_util

# Enable logging
logger = logging.getLogger(__name__)

# Handle /start
def start(bot, update):

    # bakchod_util.bakchod_updater(update.message.from_user)

    logger.info('/start: Handling /start response')
    logger.info("Request from user '%s' in group '%s'", update.message.from_user['username'], update.message.chat.title)
    update.message.reply_text(util.random_reply())


# Handle erros
def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)


# Handle all text messages received
def all_text(bot, update):

    # logger.info("all_text: Received text message from user '%s' in group '%s'", update.message.from_user['username'], update.message.chat.title)

    bakchod_util.bakchod_updater(update.message.from_user)
    
    message_text = update.message.text

    # TODO: Handle this through custom filters
    if(message_text == 'hi' or message_text == 'Hi'):
        hi_handler.handle(bot, update)

    # Handle bestie messages
    if "bestie" in message_text:
        bestie_handler.handle(bot, update)

def all_commands(bot, update):

    command_list = macro_handler.get_macros_keys()

    message_text = update.message.text

    for command in command_list:
        if message_text.startswith(command):
            logger.info("We In - %s", command)
            macro_handler.handle(bot, update, command)

# Handle all text messages received
def all_sticker(bot, update):

    # logger.info("all_sticker: Received Sticker Message from user '%s' in group '%s'", update.message.from_user['username'], update.message.chat.title)
    
    bakchod_util.bakchod_updater(update.message.from_user)
