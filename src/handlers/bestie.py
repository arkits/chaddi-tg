#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
import random
from datetime import datetime

# Enable logging
logger = logging.getLogger(__name__)

bestie_response_whitelist = [222021705, 148933790]


# Handler bestie
def handle(bot, update):

    if(update.message.from_user['id'] in bestie_response_whitelist):
        logger.info("/bestie: Handling /bestie request from user '%s' in group '%s'", update.message.from_user['username'], update.message.chat.title)
        update.message.reply_text(random_reply())


# Shoot a reply
def random_reply():
    
    replies = ['gussa aa ri', 'nhi ho ra', 'chid chid ho ra', 'mere friend ban jao fir se', 'pukish hora', 'headache ho ra']

    random.seed(datetime.now())
    random_int = random.randint(0,len(replies)-1)

    return(replies[random_int])
