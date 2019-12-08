#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
from util import bakchod_util
from util import chaddi_util
import ffmpeg
import datetime

# Enable logging
logger = logging.getLogger(__name__)


# Convert Webm to mp4
def handle(bot, update):
    
    logger.info("webm: Handling webm request from user '%s' in group '%s'", update.message.from_user['username'], update.message.chat.title)

    document = update.message.document

    if document.file_name.endswith(".webm"):

        logger.info("webm: Got a webm - " + str(document.file_id))

        time_before = datetime.datetime.now()

        try:
            # Download the webm file
            webm_file = bot.get_file(document.file_id)
            webm_file.download('resources/to_convert.webm')
            logger.info("Downloaded webm - " + str(document.file_id))

            # Conversion via ffmpeg
            probe = ffmpeg.probe('resources/to_convert.webm')
            audio_probe = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)

            stream = ffmpeg.input('resources/to_convert.webm')
            video = stream.video.filter('crop', 'iw-mod(iw,2)', 'ih-mod(ih,2)')

            if audio_probe is None:
                logger.info("webm: audio_stream is none!")
                output = ffmpeg.output(video, 'resources/converted.mp4', vcodec='libx265', crf=28, acodec='libvorbis')
                output = ffmpeg.overwrite_output(output)
                ffmpeg.run(output)
            else:
                logger.info("webm: audio_stream is not none!")
                audio = stream.audio
                joined = ffmpeg.concat(video, audio, v=1, a=1).node
                output = ffmpeg.output(joined[0], joined[1], 'resources/converted.mp4', vcodec='libx265', crf=28, acodec='libvorbis')
                output = ffmpeg.overwrite_output(output)
                ffmpeg.run(output)

            # Calculate time taken
            time_after = datetime.datetime.now()
            difference = time_after - time_before
            pretty_time_delta = chaddi_util.pretty_time_delta(difference.seconds)
            logger.info("webm: Finished converting webm=%s , timeTaken=%s", str(document.file_id), pretty_time_delta)

            og_from = update.message.from_user
            if(og_from['username']):
                og_sender = "@" + og_from['username']
            elif(og_from['firstname']):
                og_sender = og_from['firstname']

            caption = document.file_name + " uploaded by " + og_sender + " has been converted to MP4 in " + str(pretty_time_delta)

            try:
                bot.delete_message(
                    chat_id=update.message.chat_id,
                    message_id=update.message.message_id
                )
            except:
                logger.warn("webm: caught error when trying to delete")

            bot.send_video(
                chat_id=update.message.chat_id,
                video=open('resources/converted.mp4', 'rb'),
                timeout=5000,
                caption=caption
            )
            
        except Exception as e:
            
            logger.error("webm: Caught error in webm_converter - %s", e)

            response = "Error occured during WebM conversion - `" + str(e) + "`"
            update.message.reply_text(
                text=response, 
                parse_mode=ParseMode.MARKDOWN
            )
