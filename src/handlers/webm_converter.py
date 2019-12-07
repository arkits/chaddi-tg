#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
from util import bakchod_util
import ffmpeg
import datetime

# Enable logging
logger = logging.getLogger(__name__)


# Convert Webm to mp4
def handle(bot, update):
    
    logger.info("webm: Handling webm request from user '%s' in group '%s'", update.message.from_user['username'], update.message.chat.title)

    document = update.message.document

    if document.file_name.endswith(".webm"):

        logger.info("Got a webm - " + str(document.file_id))

        time_before = datetime.datetime.now()
        webm_file = bot.get_file(document.file_id)
        webm_file.download('resources/to_convert.webm')
        logger.info("Downloaded webm - " + str(document.file_id))

        stream = ffmpeg.input('resources/to_convert.webm')
        video = stream.video.filter('crop', 'iw-mod(iw,2)', 'ih-mod(ih,2)')
        audio = stream.audio
        joined = ffmpeg.concat(video, audio, v=1, a=1).node
        output = ffmpeg.output(joined[0], joined[1], 'resources/converted.mp4',vcodec='libx265', crf=28, acodec='libvorbis')
        output = ffmpeg.overwrite_output(output)
        ffmpeg.run(output)

        logger.info("Finished converting webm - " + str(document.file_id))

        time_after = datetime.datetime.now()
        difference = time_after - time_before
        minutes = int(difference.seconds/60)
        seconds = difference.seconds%60
        og_from = update.message.from_user

        if(og_from['username']):
            og_sender = "@" + og_from['username']
        elif(og_from['firstname']):
            og_sender = og_from['firstname']

        caption = document.file_name + " uploaded by " + og_sender + " has been converted to MP4 in " + str(minutes) + " minutes " + str(seconds) + " seconds"

        update.message.reply_video(video=open('resources/converted.mp4', 'rb'), timeout=5000, caption=caption)
