#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode

import os
import config
from gtts import gTTS
import bakchod_util

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

soundboard_dict = {
    "saale main teri gaand maar dunga" : "resources/saale.mp3"
}

 # Handle /tts
def handle(bot, update):

    bakchod_util.bakchod_updater(update.message.from_user['username'])

    logger.info("/tts: Handling /tts request from user '%s' in group '%s'", update.message.from_user['username'], update.message.chat.title)

    query = update.message.text
    query = query[5:]
    query = query.lower()
    query = query.strip()

    if(update.message.reply_to_message):
        query = update.message.reply_to_message.text
        query = query.lower()
        query = query.strip()

        logger.info('/tts query size: %s. query text: %s', len(query), query)

        if len(query) < 1000:

            if query in soundboard_dict.keys():
                logger.info("Found query in soundboard_dict")
                file_to_send = soundboard_dict[query]
            else:
                logger.info("Not found query in soundboard_dict")
                file_to_send = tts_util(query)

            if file_to_send is not None:
                update.message.reply_to_message.reply_voice(voice=open(file_to_send, 'rb'), timeout=5000)
                
    else:

        query = update.message.text
        query = query[5:]
        query = query.lower()
        query = query.strip()

        logger.info('/tts query size: %s. query text: %s', len(query), query)

        if len(query) < 1000:

            if query in soundboard_dict.keys():
                logger.info("Found query in soundboard_dict")
                file_to_send = soundboard_dict[query]
            else:
                logger.info("Not found query in soundboard_dict")
                file_to_send = tts_util(query)

            if file_to_send is not None:
                update.message.reply_voice(voice=open(file_to_send, 'rb'), timeout=5000)

        else:
            logger.warn('/tts: tts query is too long!')
            update.message.reply_text("HAAAAAT! Your tts query is too long!")

def tts_util(text_to_convert):

    outputFile = None

    if config.tts_engine == "gTTS":
        outputFile = 'output.mp3'
        tts = gTTS(text_to_convert, lang='en')
        tts.save(outputFile)

    elif config.tts_engine == "festival":
        outputFile = 'output.wav'
        os.system('echo %s | text2wave -o output.wav' % text_to_convert)

    else:
        logger.error("tts_engine was not set in config.py!")

    return outputFile