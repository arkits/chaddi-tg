#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode

import util
import handlers.hi as hi_handler
import handlers.bestie as bestie_handler
import handlers.macro as macro_handler
import handlers.webm_converter as webm_handler
from util import bakchod_util
from util import group_util

# Enable logging
logger = logging.getLogger(__name__)

# Handle /start
def start(bot, update):

    bakchod_util.bakchod_updater(update.message.from_user)

    logger.info('/start: Handling /start response')
    logger.info("Request from user '%s' in group '%s'", update.message.from_user['username'], update.message.chat.title)
    update.message.reply_text(util.random_reply())


# Handle erros
def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)


# Handle all text messages received
def all_text(bot, update):

    if censor_check(bot, update):
        return

    bakchod_util.bakchod_updater(update.message.from_user)
    group_util.group_updater(update.message.chat, update.message.from_user)
    
    message_text = update.message.text

    # Handle 'hi' messages
    if(message_text == 'hi' or message_text == 'Hi'):
        hi_handler.handle(bot, update)

    # Handle bestie messages
    if "bestie" in message_text.lower():
        bestie_handler.handle(bot, update)


# Handle all /commands received
def all_commands(bot, update):

    if censor_check(bot, update):
        return

    command_list = macro_handler.get_macros_keys()

    message_text = update.message.text

    for command in command_list:
        if message_text.startswith(command):
            macro_handler.handle(bot, update, command)


# Handle all_videos received
def all_videos(bot, update):

    if censor_check(bot, update):
        return

    bakchod_util.bakchod_updater(update.message.from_user)

    webm_handler.handle(bot, update)


# Handle all_stickers received
def all_stickers(bot, update):
    
    if censor_check(bot, update):
        return

    bakchod_util.bakchod_updater(update.message.from_user)


# Handle all_other_messages received
def all_other_messages(bot, update):

    if censor_check(bot, update):
        return

    bakchod_util.bakchod_updater(update.message.from_user)


# Checks whether the Bakchod is set to be censored.
# If censored, delete the message and return True.
def censor_check(bot, update):

    censored = False
    
    bakchod = bakchod_util.get_bakchod(update.message.from_user['id'])

    if bakchod is not None:
        try:
            if bakchod.censored:
                logger.info("censoring id='%s' message='%s'",update.message.from_user['id'], update.message.text)
                bot.delete_message(
                    chat_id=update.message.chat_id,
                    message_id=update.message.message_id
                )
                censored = True
        except Exception as e:
            logger.debug(e)

    return censored
