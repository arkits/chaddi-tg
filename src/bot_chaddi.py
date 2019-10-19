#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Telegram bot library specific
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode

# For messagequeue
import telegram.bot
from telegram.ext import messagequeue as mq
from telegram.utils.request import Request

# Other required stuff
import logging
import random
from datetime import datetime

# Helper utils 
import config

# New Handlers
import handlers.default as default_handler
import handlers.hi as hi_handler
import handlers.bakchod as bakchod_handler
import handlers.chutiya as chutiya_handler
import handlers.tts as tts_handler
import handlers.superpower as superpower_handler
import handlers.jyotish as jyotish_handler
import handlers.mom as mom_handler
import handlers.webm_converter as webm_handler

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Test logging
logger.info("~~~~ ~~~~ ~~~~ ~~~~")
logger.info("ChaddiBot")
logger.info("~~~~ ~~~~ ~~~~ ~~~~")


class ChaddiBot(telegram.bot.Bot):

    # Custom Bot class which delegates send method handling to MQ

    def __init__(self, *args, is_queued_def=True, mqueue=None, **kwargs):
        super(ChaddiBot, self).__init__(*args, **kwargs)

        # Below 2 attributes should be provided for decorator usage
        self._is_messages_queued_default = is_queued_def
        self._msg_queue = mqueue or mq.MessageQueue()

    def __del__(self):
        try:
            self._msg_queue.stop()
        except:
            pass
        super(ChaddiBot, self).__del__()

    @mq.queuedmessage
    def send_message(self, *args, **kwargs):
        return super(ChaddiBot, self).send_message(*args, **kwargs)


def main():

    q = mq.MessageQueue(all_burst_limit=3, all_time_limit_ms=3000)

    token = config.tg_bot_token

    request = Request(con_pool_size=8)
    chaddiBot = ChaddiBot(token, request=request, mqueue=q)
    updater = telegram.ext.updater.Updater(bot=chaddiBot)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # /commands
    dp.add_handler(CommandHandler("hi", hi_handler.handle))
    dp.add_handler(CommandHandler("superpower", superpower_handler.handle))
    dp.add_handler(CommandHandler("tts", tts_handler.handle))
    dp.add_handler(CommandHandler("chutiya", chutiya_handler.handle))
    dp.add_handler(CommandHandler("timesince", bakchod_handler.timesince))
    dp.add_handler(CommandHandler("rokda", bakchod_handler.rokda))
    dp.add_handler(CommandHandler("jyotish", jyotish_handler.handle))
    dp.add_handler(CommandHandler("mom", mom_handler.handle))

    # regular messages
    dp.add_handler(MessageHandler(Filters.text, default_handler.all_text))
    dp.add_handler(MessageHandler(Filters.sticker, default_handler.all_sticker))
    dp.add_handler(MessageHandler(Filters.document.category("video"), webm_handler.handle))

    # log all errors
    dp.add_error_handler(default_handler.error)

    # Start the Bot

    if config.is_dev:
        updater.start_polling()
    else:
        updater.start_webhook(listen='127.0.0.1', port=5000, url_path='TOKEN1')
        updater.bot.set_webhook(url=config.tg_webhook_url)

    logger.info("Running...")
    logger.info("~~~~ ~~~~ ~~~~ ~~~~")
    
    updater.idle()

if __name__ == '__main__':
    main()
