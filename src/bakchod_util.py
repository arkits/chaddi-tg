#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ChaddiBot
https://ghati.bitbucket.io/
"""

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode

import logging
import pickle
import util
from datetime import datetime, date, timezone

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class Bakchod:
  def __init__(self, username):
    self.username = username
    self.lastseen = 0
    self.lakshmi = 0

try:
    with open('resources/bakchod.pickle', 'rb') as handle:
        bakchod_dict = pickle.load(handle)
        logger.info('Loaded Bakchod pickle')
except:
    logger.info('Bakchod pickle not found... Making new one')
    bakchod_dict = {}
    with open('resources/bakchod.pickle', 'wb') as handle:
        pickle.dump(bakchod_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

def bakchod_updater(from_user):

    if from_user is not None:
        from_user = "@" + from_user

        if from_user in bakchod_dict:
            a_bakchod = bakchod_dict[from_user]
        else:
            a_bakchod = Bakchod(from_user)

        a_bakchod.lastseen = datetime.now()
        a_bakchod.lakshmi = a_bakchod.lakshmi + 1

        logger.info("Updating Bakchod for username=" + from_user + " rokda=" + str(a_bakchod.lakshmi))

        bakchod_dict[from_user] = a_bakchod

        with open('resources/bakchod.pickle', 'wb') as handle:
            pickle.dump(bakchod_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
        
def timesince_query(query_username):

    if query_username[0] != "@":
        query_username = "@" + query_username

    if query_username in bakchod_dict:
        found_bakchod = bakchod_dict[query_username]
        response = timesince_calculator(found_bakchod.lastseen)
        return(query_username + ' last posted ' + response + ' ago')
    else: 
        return("404")

def timesince_calculator(lastseen):
    now = datetime.now()
    td = now - lastseen
    pretty_td = util.pretty_time_delta(td.total_seconds())
    return(pretty_td)

def lakshmi_query(query_username):

    if query_username[0] != "@":
        query_username = "@" + query_username

    if query_username in bakchod_dict:
        found_bakchod = bakchod_dict[query_username]
        response = found_bakchod.lakshmi
        return("💰" + query_username + ' has ' + str(response) + ' ₹okda!')
    else: 
        return("404")