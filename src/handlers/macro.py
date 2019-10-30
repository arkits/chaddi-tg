#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
import pickle

# Enable logging
logger = logging.getLogger(__name__)

# Using Python pickling for data persistence
try:
    with open('resources/macros.pickle', 'rb') as handle:
        macro_dict = pickle.load(handle)
        logger.info('Loaded Macros pickle')
except:
    logger.info('Macros pickle not found... Making new one')
    macro_dict = {}
    with open('resources/macros.pickle', 'wb') as handle:
        pickle.dump(macro_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

# Handler Macro
def handle(bot, update, key):

    logger.info("macro: Handling Macro request from user '%s' in group '%s'",
                update.message.from_user['username'], update.message.chat.title)

    macro = macro_dict[key]

    if macro['is_sticker']:
        update.message.reply_sticker(sticker=macro['data'])
    else:
        update.message.reply_text(text=macro['data'])

def add_to_macros(key, macro):

    macro_dict[key] = macro

    with open('resources/macros.pickle', 'wb') as handle:
        pickle.dump(macro_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

def get_macros_keys():

    return list(macro_dict.keys())
