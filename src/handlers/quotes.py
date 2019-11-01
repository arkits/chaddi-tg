#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode

import logging
import pickle
import util
import random
from datetime import datetime

# Enable logging
logger = logging.getLogger(__name__)

# Using Python pickling for data persistence
try:
    with open('resources/quotes.pickle', 'rb') as handle:
        quotes_list = pickle.load(handle)
        logger.info('Loaded Quotes pickle')
except:
    logger.info('Quotes pickle not found... Making new one')
    quotes_list = []
    with open('resources/quotes.pickle', 'wb') as handle:
        pickle.dump(quotes_list, handle, protocol=pickle.HIGHEST_PROTOCOL)

def handle(bot, update):

    logger.info("/quotes: Handling /quotes request from user '%s' in group '%s'", update.message.from_user['username'], update.message.chat.title)

    # Extract query...
    query = update.message.text
    query = query[7:]
    query = query.lower()
    query = query.strip()

    if query == "add":
        
        # Handle '/quotes add
        # Add the quoted message to quotes_list
        if update.message.reply_to_message.text:

            quoted_message = update.message.reply_to_message.text

            if update.message.reply_to_message.from_user['username']:
                quoted_user = update.message.reply_to_message.from_user['username']
            else:
                quoted_user = update.message.reply_to_message.from_user['first_name']

            quoted_date = update.message.reply_to_message.date
            
            quote = {
                'message' : quoted_message,
                'user' : quoted_user,
                'date' : quoted_date
            }

            quotes_list.append(quote)
            logger.info("/quotes: Added Quoted Message to quotes_list[%s] - %s", len(quotes_list), quoted_message)

            with open('resources/quotes.pickle', 'wb') as handle:
                pickle.dump(quotes_list, handle, protocol=pickle.HIGHEST_PROTOCOL)

        update.message.reply_text(
            text="Rote memorization successful", 
            parse_mode=ParseMode.MARKDOWN
            )

    else:

        # Return a random quote
        random_quote = get_random_quote()

        logger.info("/quotes: Returning a random quote '%s'", random_quote)

        pretty_quote = "`" + random_quote['message'] + "` \n - @" + random_quote['user']

        update.message.reply_text(
            text=pretty_quote, 
            parse_mode=ParseMode.MARKDOWN
        )

# Returns a random quote
def get_random_quote():

    random.seed(datetime.now())
    random_int = random.randint(0, len(quotes_list)-1)

    return(quotes_list[random_int])