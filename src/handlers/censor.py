#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
from util import bakchod_util
import config

# Enable logging
logger = logging.getLogger(__name__)

# Handler censor
def handle_censor(bot, update):
    if is_admin(update.message.from_user['id']):
        if update.message.reply_to_message:
            response = process_user(update, True)
            update.message.reply_to_message.reply_text(
                text=response,
                parse_mode=ParseMode.HTML
            )
    else:
        if update.message.reply_to_message:
            update.message.reply_to_message.reply_text(
                text="❌ Not allowed censor",
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
    if is_admin(update.message.from_user['id']):
        if update.message.reply_to_message:
            response = process_user(update, False)
            update.message.reply_to_message.reply_text(
                text=response,
                parse_mode=ParseMode.HTML
            )
    else:
        update.message.reply_to_message.reply_text(
            text="❌ Not allowed uncensor",
            parse_mode=ParseMode.HTML
        )


def process_user(update, to_censor):

    user_id = update.message.reply_to_message.from_user['id']
    if update.message.reply_to_message.from_user['username']:
        username = "@" + update.message.reply_to_message.from_user['username']
    else:
        username = update.message.reply_to_message.from_user['first_name']

    a_bakchod = bakchod_util.get_bakchod(user_id)

    if to_censor:
        a_bakchod.censored = True
        logger.info("/censor: request for %s", username)
        response = "☢️ Censoring " + username + "!"
    else:
        a_bakchod.censored = False
        logger.info("/uncensor: request for %s", username)
        response = "☢️ Uncensoring " + username + "!"

    bakchod_util.set_bakchod(a_bakchod)

    return response


def is_admin(og_bakchod):
    if str(og_bakchod) in config.allowed_setters:
        logger.info("is_admin: og_bakchod in config.allowed_setters")
        return True
    else:
        return False
