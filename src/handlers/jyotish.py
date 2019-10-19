#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode

import util
import bakchod_util
import requests
import json

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

url = "https://8ball.delegator.com/magic/JSON/"


# Handle /jyotish
def handle(bot, update):

    logger.info(update)

    if(update.message.reply_to_message):

        query = update.message.reply_to_message.text
        query = query.lower()
        query = query.strip()

        if len(query) <= 0:
            query = "Empty"

        logger.info("/hi: Handling /jyotish request from user '%s' in group '%s'. Query- %s.", update.message.from_user['username'], update.message.chat.title, query)

        query_url = url + query

        response = requests.request("GET", query_url)
        response = json.loads(response.text)

        if response['magic']['answer']:
            update.message.reply_to_message.reply_text(response['magic']['answer'])
        else:
            update.message.reply_to_message.reply_text("hmmmm")

    else:
        query = update.message.text
        query = query[9:]
        query = query.lower()
        query = query.strip()

        if len(query) > 0:

            logger.info("/hi: Handling /jyotish request from user '%s' in group '%s'. Query- %s.", update.message.from_user['username'], update.message.chat.title, query)
        
            query_url = url + query

            response = requests.request("GET", query_url)
            response = json.loads(response.text)

            if response['magic']['answer']:
                update.message.reply_text(response['magic']['answer'])
            else:
                update.message.reply_text("nahhhhh.....")
                
        else:
            update.message.reply_text("haaaat bc")

