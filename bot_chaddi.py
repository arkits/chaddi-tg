#!/usr/bin/env python
# -*- coding: utf-8 -*-

###################################################################
#                         ChaddiBot                               #
#                        Archit Khode                             #
###################################################################

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
import handlers

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

    # Create the EventHandler and pass it your bot's token.
    # updater = Updater(config.tg_bot_token)

    # Uncomment the following block for job_spam
    # jq = updater.job_queue
    # if config.is_dev is False:
    #    logger.info('is_dev is False')
    #    jq.run_repeating(job_spam, 20*60)
    # else:
    #    logger.info('is_dev is True')
    #    jq.run_repeating(job_spam, 1*60)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # /commands
    dp.add_handler(CommandHandler("start", handlers.start))
    dp.add_handler(CommandHandler("hi", handlers.hi))
    dp.add_handler(CommandHandler("timesince", handlers.timesince))
    dp.add_handler(CommandHandler("superpower", handlers.superpower))

    # regular messages
    dp.add_handler(MessageHandler(Filters.text, handlers.all_text))
    dp.add_handler(MessageHandler(Filters.sticker, handlers.all_sticker))

    # log all errors
    dp.add_error_handler(handlers.error)

    # Start the Bot
    updater.start_polling()
    logger.info("Started Polling...")
    logger.info("~~~~ ~~~~ ~~~~ ~~~~")
    
    updater.idle()

if __name__ == '__main__':
    main()