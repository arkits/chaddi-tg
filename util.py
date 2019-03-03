#!/usr/bin/env python
# -*- coding: utf-8 -*-

###################################################################
#                         ChaddiBot                               #
#                        Archit Khode                             #
###################################################################


from datetime import datetime, date
import random
from datetime import datetime
import pickle
import logging

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
        logger.info('Saved pickle')

def timesince_updater(from_user):
    from_user = "@" + from_user
    logger.info("Updating timesince for: " + from_user)
    time_since_dict[from_user] = datetime.now()

    with open('timesince.pickle', 'wb') as handle:
        pickle.dump(time_since_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
        logger.info('Saved pickle')

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

"""
def random_user(group_name): # Retired
    random.seed(datetime.now())

    if(group_name=='true'):
        users = ['@Dhruva93', '@Urushibara', '@pahagwl', '@ChocoBuns', '@Grape_hunter', '@arkits', '@ArmoredKuruma']
        random_int = random.randint(0,len(users)-1)
        return(users[random_int])

    elif(group_name=='mains'):
        users = ['@Dhruva93', '@pahagwl', '@Grape_hunter', '@arkits', '@ArmoredKuruma', '@Aurum2', '@Nathuram', '@bleachnchill', '@agentredux', '@vcidst', '@psydroid', '@themusketeer' ,'@vogonpoet', '@t0otSie', '@nitrobeer', '@Rrrik', '@woosteresque', '@QuizMasterAsh']
        random_int = random.randint(0,len(users)-1)
        return(users[random_int])
"""

"""
def awk_timer(): # Retired
    now = datetime.now()
    rip_day = datetime(year = 2019, month = 2, day = 6, hour = 5, minute = 31, second = 00)
    td = now - rip_day
    pretty_td = pretty_time_delta(td.total_seconds())
    return(pretty_td)
"""
