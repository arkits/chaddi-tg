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
from datetime import time

# Helper utils 
import config
import util.logger

# New Handlers
import handlers.default as default_handler
import handlers.hi as hi_handler
import handlers.bakchod as bakchod_handler
import handlers.choose as choose_handler
import handlers.chutiya as chutiya_handler
import handlers.help as help_handler
import handlers.tts as tts_handler
import handlers.superpower as superpower_handler
import handlers.jyotish as jyotish_handler
import handlers.mom as mom_handler
import handlers.quotes as quotes_handler
import handlers.setter as setter_handler
import handlers.birthday as birthday_handler
import handlers.gamble as gamble_handler
import handlers.me as me_handler
import handlers.calc as calc_handler
import handlers.censor as censor_handler

logger = util.logger.get_logger(__name__)

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

    jq = updater.job_queue

    birthday_job_time = time(hour=10, minute=0, second=0, microsecond=0, tzinfo=None)
    # jq.run_repeating(birthday_handler.daily_job, 5)
    jq.run_daily(birthday_handler.daily_job, birthday_job_time)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # /commands
    dp.add_handler(CommandHandler("hi", hi_handler.handle))
    dp.add_handler(CommandHandler("superpower", superpower_handler.handle))
    dp.add_handler(CommandHandler("tts", tts_handler.english_tts))
    dp.add_handler(CommandHandler("ghati", tts_handler.hindi_tts))
    dp.add_handler(CommandHandler("chutiya", chutiya_handler.handle))
    dp.add_handler(CommandHandler("timesince", bakchod_handler.timesince))
    dp.add_handler(CommandHandler("rokda", bakchod_handler.rokda))
    dp.add_handler(CommandHandler("jyotish", jyotish_handler.handle))
    dp.add_handler(CommandHandler("mom", mom_handler.handle))
    dp.add_handler(CommandHandler("quotes", quotes_handler.handle))
    dp.add_handler(CommandHandler("quote", quotes_handler.handle))
    dp.add_handler(CommandHandler("help", help_handler.handle))
    dp.add_handler(CommandHandler("choose", choose_handler.handle))
    dp.add_handler(CommandHandler("about", bakchod_handler.about))
    dp.add_handler(CommandHandler("birthday", birthday_handler.handle))
    dp.add_handler(CommandHandler("birthdays", birthday_handler.handle))
    dp.add_handler(CommandHandler("set", setter_handler.handle))
    dp.add_handler(CommandHandler("gamble", gamble_handler.handle))
    dp.add_handler(CommandHandler("me", me_handler.handle))
    dp.add_handler(CommandHandler("calc", calc_handler.handle))
    dp.add_handler(CommandHandler("censor", censor_handler.handle_censor))
    dp.add_handler(CommandHandler("uncensor", censor_handler.handle_uncensor))

    # regular messages
    dp.add_handler(MessageHandler(Filters.text, default_handler.all_text))
    dp.add_handler(MessageHandler(Filters.command, default_handler.all_commands))
    dp.add_handler(MessageHandler(Filters.sticker, default_handler.all_stickers))
    dp.add_handler(MessageHandler(Filters.document.category("video"), default_handler.all_videos))
    dp.add_handler(MessageHandler(Filters.all, default_handler.all_other_messages))

    # log all errors
    dp.add_error_handler(default_handler.error)

    # Start the Bot
    try:
        webhook_url = config.tg_webhook_url
        logger.info("config: tg_webhook_url is set to '%s'... using webhook for connectivity", webhook_url)
        updater.start_webhook(listen='127.0.0.1', port=5000, url_path='TOKEN1')
        updater.bot.set_webhook(url=webhook_url)
    except:
        logger.info("config: tg_webhook_url is not set... using polling for connectivity")
        updater.start_polling()

    logger.info("Running...")
    logger.info("~~~~ ~~~~ ~~~~ ~~~~")

    updater.idle()

if __name__ == '__main__':
    main()
