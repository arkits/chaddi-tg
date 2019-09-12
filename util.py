#!/usr/bin/env python
# -*- coding: utf-8 -*-

###################################################################
#                         ChaddiBot                               #
#                        Archit Khode                             #
###################################################################

import os
import random
import pickle
import logging
import config
import pytz
from datetime import datetime, date, timezone
from gtts import gTTS

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    with open('timesince.pickle', 'rb') as handle:
        time_since_dict = pickle.load(handle)
        logger.info('Loaded pickle')
except:
    logger.info('Pickle not found... making new one')
    time_since_dict = {}
    with open('timesince.pickle', 'wb') as handle:
        pickle.dump(time_since_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
        logger.debug('Saved pickle')

def timesince_updater(from_user):
    from_user = "@" + from_user
    logger.debug("Updating timesince for: " + from_user)
    time_since_dict[from_user] = datetime.now()

    with open('timesince.pickle', 'wb') as handle:
        pickle.dump(time_since_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
        logger.debug('Saved pickle')

def timesince_query(query_username):
    if query_username in time_since_dict:
        response = timesince_calculator(time_since_dict[query_username])
        return(query_username + ' last posted ' + response + ' ago')
    else: 
        return("404")

def timesince_calculator(lastseen):
    now = datetime.now()
    td = now - lastseen
    pretty_td = pretty_time_delta(td.total_seconds())
    return(pretty_td)

def random_reply():
    replies = ['hi', 'bc', 'mmll', '...', '🙏 NAMASKAR MANDALI 🙏']
    random.seed(datetime.now())
    random_int = random.randint(0,len(replies)-1)
    return(replies[random_int])

def pretty_time_delta(seconds):
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return '%dd %dh %dm %ds' % (days, hours, minutes, seconds)
    elif hours > 0:
        return '%dh %dm %ds' % (hours, minutes, seconds)
    elif minutes > 0:
        return '%dm %ds' % (minutes, seconds)
    else:
        return '%ds' % (seconds,)

def superpower_countdown_calc():
    # Calculates timedelta between current time and Dec 31st 2019 IST.

    ist = pytz.timezone("Asia/Kolkata")
    
    # Current time in IST
    now = datetime.now(ist)
    
    # Dec 31 in IST
    superpower_day = datetime(year = 2020, month = 1, day = 1, hour = 0, minute = 0, second = 0, tzinfo = ist)
    
    # Get timedelta
    td = superpower_day - now
    pretty_td = pretty_time_delta(td.total_seconds())

    return(pretty_td)

def tts_util(text_to_convert):

    outputFile = None

    if config.tts_engine == "gTTS":
        outputFile = 'output.mp3'
        tts = gTTS(text_to_convert, lang='en')
        tts.save(outputFile)

    elif config.tts_engine == "festival":
        outputFile = 'output.wav'
        os.system('echo %s | text2wave -o output.wav' % text_to_convert)

    else:
        logger.error("tts_engine was not set in config.py!")

    return outputFile