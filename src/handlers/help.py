#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from telegram import ParseMode


# Enable logging
logger = logging.getLogger(__name__)


# Handler help
def handle(bot, update):

    logger.info("/help: Printing help message for user='%s' in group='%s'", update.message.from_user['username'], update.message.chat.title)

    help_message =  "🙏🙏🙏 <b>ChaddiBot Help</b> 🙏🙏🙏" \
                    " \n \n " \
                    " <i>Available commands:</i> \n" \
                    " <code>/superpower</code> - Returns the time until New Year 2020. \n" \
                    " <code>/tts {text}</code> - Converts passed {text} into speech. \n" \
                    " <code>/ghati {text}</code> - Converts passed {text} into Hindi speech. \n" \
                    " <code>/jyotish</code> Tries to solve your problems of life and fails everytime. \n" \
                    " <code>/mom</code> - Insults your mom. \n "  \
                    " <code>/rokda</code> - Rokda is the currency of #Bakchodi. Shows how much Rokda you have. \n" \
                    " <code>/gamble</code> - Lets you gamble your Rokda."


    update.message.reply_text(
        text=help_message,
        parse_mode=ParseMode.HTML
    )
