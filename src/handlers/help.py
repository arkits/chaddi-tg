#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# Handler help
def handle(bot, update):
    logger.info("/help: Print help message")

    help_message = "BOT USAGE: '/ + command' \n" \
                   "Available commands: \n"\
                   "/hi or /Hi --- Say hi to you \n"\
                   "/superpower --- return time until New Year \n"\
                   "/tts --- \n"\
                   "/ghati --- \n"\
                   "/chutiya --- \n"\
                   "/timesince --- Given a user name, return last login time\n"\
                   "/rokda --- \n"\
                   "/jyotish --- \n"\
                   "/mom --- \n"\
                   "/quotes --- \n" \
                   "/choose --- Given a list of options separated by comma or newline, return one of them"
    update.message.reply_text(help_message)
