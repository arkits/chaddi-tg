#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import random


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# Handler choose
def handle(bot, update):
    logger.info("/choose: Handling /choose request")
    update.message.reply_text(random_reply(update.message))


def random_reply(message):
    message = message['text'].split(' ')
    return random.choice(message[1:])
