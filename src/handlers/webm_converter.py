#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
import bakchod_util
import ffmpeg

# Enable logging
logger = logging.getLogger(__name__)


# Convert Webm to mp4
def handle(bot, update):

    # Update Bakchod pickle
    # bakchod_util.bakchod_updater(update.message.from_user)
    
    logger.info("webm: Handling webm request from user '%s' in group '%s'", update.message.from_user['username'], update.message.chat.title)

    document = update.message.document

    if document.file_name.endswith(".webm"):

        logger.info("Got a webm - " + str(document.file_id))

        webm_file = bot.get_file(document.file_id)
        webm_file.download('resources/to_convert.webm')
        logger.info("Downloaded webm - " + str(document.file_id))

        stream = ffmpeg.input('resources/to_convert.webm')
        stream = ffmpeg.output(stream, 'resources/converted.mp4')
        stream = ffmpeg.overwrite_output(stream)
        ffmpeg.run(stream)
        logger.info("Finished converting webm - " + str(document.file_id))

        og_from = update.message.from_user

        if(og_from['username']):
            og_sender = "@" + og_from['username']
        elif(og_from['firstname']):
            og_sender = og_from['firstname']

        caption = "madarchod " + og_sender + " kal se webm cancel!"

        update.message.reply_video(video=open('resources/converted.mp4', 'rb'), timeout=5000, caption=caption)
