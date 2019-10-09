#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
import random
from datetime import datetime
import bakchod_util

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Handler hi
def handle(bot, update):

    bakchod_util.bakchod_updater(update.message.from_user['username'])
    
    hi_response_whitelist = ["pahagwl", "arkits"]

    if(update.message.from_user['username'] in hi_response_whitelist):
        logger.info("/hi: Handling /hi request from user '%s' in group '%s'", update.message.from_user['username'], update.message.chat.title)
        update.message.reply_text(random_reply())

def random_reply():

    replies = ['hi', 'bc', 'mmll', '...', '🙏 NAMASKAR MANDALI 🙏']
    
    random.seed(datetime.now())
    random_int = random.randint(0,len(replies)-1)

    return(replies[random_int])