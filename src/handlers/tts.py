#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode

import os
import config
from gtts import gTTS
from util import bakchod_util

# Enable logging
logger = logging.getLogger(__name__)

soundboard_dict = {
    "saale main teri gaand maar dunga" : "resources/saale.mp3"
}


def english_tts(bot, update):
    handle(bot, update, "en")


def hindi_tts(bot, update):
    handle(bot, update, "hi")


 # Handle /tts
def handle(bot, update, language):

    # Update Bakchod pickle
    # bakchod_util.bakchod_updater(update.message.from_user)

    logger.info("/tts: Handling /tts request from user '%s' in group '%s'", update.message.from_user['username'], update.message.chat.title)


    if(update.message.reply_to_message):

        # Handle quoted message...
        query = update.message.reply_to_message.text
        query = query.strip()

        logger.info('/tts query size: %s. query text: %s', len(query), query)

        perform_tts(query, update)
                
    else:

        # Handle original user's message...
        query = update.message.text
        query = query.split(' ')
        query = ' '.join(query[1:])
        query = query.strip()

        logger.info('/tts query size: %s. query text: %s', len(query), query)

        perform_tts(query, update)


def perform_tts(query, update):

    if len(query) < 1000:

        if query in soundboard_dict.keys():
            logger.debug("Found query in soundboard_dict")
            file_to_send = soundboard_dict[query]
        else:
            logger.debug("Not found query in soundboard_dict")
            file_to_send = tts_util(query, language)

        if file_to_send is not None:
            if(update.message.reply_to_message):
                update.message.reply_to_message.reply_voice(voice=open(file_to_send, 'rb'), timeout=5000)
            else:
                update.message.reply_voice(voice=open(file_to_send, 'rb'), timeout=5000)

    else:
        logger.warn('/tts: tts query is too long!')
        update.message.reply_text("HAAAAAT! Your tts query is too long!")


def tts_util(text_to_convert, language):

    outputFile = None

    if config.tts_engine == "gTTS":
        
        outputFile = 'resources/gtts_output.mp3'
        tts = gTTS(text_to_convert, lang=language)
        tts.save(outputFile)

    else:
        logger.error("tts_engine was not set in config.py!")

    return outputFile
