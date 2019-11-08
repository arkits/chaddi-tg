#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
import random
from datetime import datetime
from util import bakchod_util

# Enable logging
logger = logging.getLogger(__name__)


# Handler hi
def handle(bot, update):

    # Update Bakchod pickle
    # bakchod_util.bakchod_updater(update.message.from_user)
    
    hi_response_whitelist = ["pahagwl", "arkits", "volis2"]

    if(update.message.from_user['username'] in hi_response_whitelist):
        logger.info("/hi: Handling /hi request from user '%s' in group '%s'", update.message.from_user['username'], update.message.chat.title)
        update.message.reply_text(random_reply())


def random_reply():

    replies = ['hi', 'bc', 'mmll', '...', '🙏 NAMASKAR MANDALI 🙏']
    
    random.seed(datetime.now())
    random_int = random.randint(0,len(replies)-1)

    return(replies[random_int])
