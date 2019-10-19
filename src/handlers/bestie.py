#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
import random
from datetime import datetime

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

bestie_response_whitelist = ['ArmoredKuruma']


# Handler bestie
def handle(bot, update):

    if(update.message.from_user['username'] in bestie_response_whitelist):
        logger.info("/bestie: Handling /bestie request from user '%s' in group '%s'", update.message.from_user['username'], update.message.chat.title)
        update.message.reply_text(random_reply())


# Shoot a reply
def random_reply():
    
    replies = ['gussa aa ri', 'nhi ho ra']

    random.seed(datetime.now())
    random_int = random.randint(0,len(replies)-1)

    return(replies[random_int])
