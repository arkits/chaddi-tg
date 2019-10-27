#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import random


# Enable logging
logger = logging.getLogger(__name__)


# Handler choose
def handle(bot, update):
    logger.info("/choose: Handling /choose request")
    update.message.reply_text(random_choice(update.message))


def random_choice(message):
    message = message['text'].split(',')
    return random.choice(message[1:])
