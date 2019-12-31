#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
from util import bakchod_util
from util import chaddi_util

# Enable logging
logger = logging.getLogger(__name__)

# Handler censor
def handle_censor(bot, update):
    if chaddi_util.is_admin(update.message.from_user['id']):

        bakchod = get_bakchod_from_context(update)

        response = process_user(bakchod, True)

        update.message.reply_text(
            text=response,
            parse_mode=ParseMode.HTML
        )

    else:
        logger.info("censoring id='%s' message='%s'",update.message.from_user['id'], update.message.text)
        
        bot.delete_message(
            chat_id=update.message.chat_id,
            message_id=update.message.message_id
        )

# Handler uncensor
def handle_uncensor(bot, update):
    if chaddi_util.is_admin(update.message.from_user['id']):

        bakchod = get_bakchod_from_context(update)

        response = process_user(bakchod, False)

        update.message.reply_text(
            text=response,
            parse_mode=ParseMode.HTML
        )

    else:

        logger.info("censoring id='%s' message='%s'",update.message.from_user['id'], update.message.text)

        bot.delete_message(
            chat_id=update.message.chat_id,
            message_id=update.message.message_id
        )


def get_bakchod_from_context(update):

    message_text = update.message.text
    message_text = message_text.split(' ')

    if message_text[1]:
        # Command with param - @username
        logger.info(message_text)
        bakchod = bakchod_util.get_bakchod_with_username(message_text[1])
    else:
        # Command without param
        user_id = update.message.reply_to_message.from_user['id']
        bakchod = bakchod_util.get_bakchod(user_id)

    return bakchod


def process_user(bakchod, to_censor):

    if to_censor:
        bakchod.censored = True
        logger.info("/censor: request for %s", bakchod.username)
        response = "☢️ Censoring " + bakchod.username + "!"
    else:
        bakchod.censored = False
        logger.info("/uncensor: request for %s", bakchod.username)
        response = "☢️ Uncensoring " + bakchod.username + "!"

    bakchod_util.set_bakchod(bakchod)

    return response
