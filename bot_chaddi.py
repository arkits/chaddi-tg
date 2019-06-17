#!/usr/bin/env python
# -*- coding: utf-8 -*-

###################################################################
#                         ChaddiBot                               #
#                        Archit Khode                             #
###################################################################

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
import logging
import random
from datetime import datetime

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("~~~~ ~~~~ ~~~~ ~~~~")
logger.info("ChaddiBot")
logger.info("~~~~ ~~~~ ~~~~ ~~~~")

import config
import handlers

def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(config.tg_bot_token)

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