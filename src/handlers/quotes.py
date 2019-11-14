#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode

import logging
import pickle
import util
import random
from datetime import datetime
import uuid 

# Enable logging
logger = logging.getLogger(__name__)

# Using Python pickling for data persistence
try:
    with open('resources/quotes.pickle', 'rb') as handle:
        quotes_dict = pickle.load(handle)
        logger.info('Loaded Quotes pickle')
except:
    logger.info('Quotes pickle not found... Making new one')
    quotes_dict = {}
    with open('resources/quotes.pickle', 'wb') as handle:
        pickle.dump(quotes_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

def handle(bot, update):

    logger.info("/quotes: Handling /quotes request from user '%s' in group '%s'", update.message.from_user['username'], update.message.chat.title)

    # Extract query...
    query = update.message.text
    query = query.split(' ')

    try:
        command = query[1]
    except:
        command = "random"

    if command == "add":
        
        if update.message.reply_to_message.text:

            response = add_quote(update)

            update.message.reply_text(
                text=response, 
                parse_mode=ParseMode.MARKDOWN
                )

    elif command == "remove":

        try:
            id_to_remove = query[2]
        except:
            update.message.reply_text(
                text="Please include the Quote ID you want to remove!", 
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        response = remove_quote(id_to_remove)

        update.message.reply_text(
            text=response, 
            parse_mode=ParseMode.MARKDOWN
        )

    else:
        # Return a random quote
        random_quote = get_random_quote()

        logger.info("/quotes: Returning a random quote '%s'", random_quote)

        pretty_quote = "`{}` \n ** - @{} ** \n - {}".format(
            random_quote['message'],
            random_quote['user'],
            random_quote['id']
        )

        update.message.reply_text(
            text=pretty_quote, 
            parse_mode=ParseMode.MARKDOWN
        )


# Add the quoted message to quotes_dict
def add_quote(update):

    quote_id = uuid.uuid1().int

    quoted_message = update.message.reply_to_message.text

    if update.message.reply_to_message.from_user['username']:
        quoted_user = update.message.reply_to_message.from_user['username']
    else:
        quoted_user = update.message.reply_to_message.from_user['first_name']

    quoted_date = update.message.reply_to_message.date
    
    quote = {
        'message' : quoted_message,
        'user' : quoted_user,
        'date' : quoted_date,
        'id' : quote_id
    }

    quotes_dict[quote_id] = quote
    logger.info("/quotes: Added Quoted Message to quotes_dict[%s] - %s", quote_id, quoted_message)

    with open('resources/quotes.pickle', 'wb') as handle:
        pickle.dump(quotes_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

    response = "✏️ Rote memorization successful! ({})".format(quote_id)
    
    return response


# Returns a random quote
def get_random_quote():

    random.seed(datetime.now())

    return(random.choice(list(quotes_dict.values())))

# Removes quote based on it's ID
def remove_quote(id_to_remove):

    try:
        id_to_remove = int(id_to_remove)

        logger.info(id_to_remove)

        logger.info(quotes_dict[id_to_remove])

        del quotes_dict[id_to_remove]

        with open('resources/quotes.pickle', 'wb') as handle:
            pickle.dump(quotes_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

        response = "Removed Quote!"

    except:

        response = "Unable to remove quote :("

    return response



