#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode

# Enable logging
logger = logging.getLogger(__name__)


# Handler /me
def handle(bot, update):

    logger.info("/me: Handling /me request from user '%s' in group '%s'",
                update.message.from_user['username'], update.message.chat.title)

    response = generate_me(update)

    if response is not None:
        logger.info("/me: response='%s'", response)

        if update.message.reply_to_message:

            # if original command was a reply to someone
            update.message.reply_to_message.reply_text(
                text=response,
                parse_mode=ParseMode.HTML
            )

        else:

            # if original command was by itself
            bot.send_message(
                chat_id=update.message.chat_id,
                message_id=update.message.message_id,
                text=response,
                parse_mode=ParseMode.HTML
            )

    # clean up waste
    bot.delete_message(
        chat_id=update.message.chat_id,
        message_id=update.message.message_id
    )


# generate a response to /me
# shoutout to the good old irc days!
def generate_me(update):

    if update.message.from_user["username"]:
        from_user = update.message.from_user["username"]
    elif update.message.from_user["firstname"]:
        from_user = update.message.from_user["firstname"]

    query = update.message.text
    query = query.split(' ')

    action = query[1:]

    if len(action) == 1:

        action = ' '.join(action)

        response = "@{} {}".format(
            from_user,
            action
        )

        response = response.strip()

    else:
        response = None

    return response
