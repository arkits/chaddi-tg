#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode

import pickle
import random
from datetime import datetime, date, timezone

import util.logger
from util import chaddi_util
from models import bakchod

# Enable logging
logger = util.logger.get_logger(__name__)

# Using Python pickling for data persistence
try:
    with open('resources/bakchod.pickle', 'rb') as handle:
        bakchod_dict = pickle.load(handle)
        logger.info('Loaded Bakchod pickle')
except:
    logger.info('Bakchod pickle not found... Making new one')
    bakchod_dict = {}
    with open('resources/bakchod.pickle', 'wb') as handle:
        pickle.dump(bakchod_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)


# Get a Bakchod based on tg_id
def get_bakchod(tg_id):

    if tg_id in bakchod_dict:
        a_bakchod = bakchod_dict[tg_id]
    else:
        a_bakchod = None

    return a_bakchod

# Get a random Bakchod
def get_bakchod_random():
    return random.choice(list(bakchod_dict.values()))


# Update Bakchod and commit to pickle
def set_bakchod(a_bakchod):

    # Make sure that rokda is always rounded to 2 decimals
    a_bakchod.rokda = round(a_bakchod.rokda, 2)

    if a_bakchod.id in bakchod_dict:
        bakchod_dict[a_bakchod.id] = a_bakchod

    with open('resources/bakchod.pickle', 'wb') as handle:
        pickle.dump(bakchod_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)


# Update data of a Bakchod... lastseen and rokda
def bakchod_updater(from_user):

    if from_user is not None:

        if from_user['username'] is not None:
            username = "@" + from_user['username']
        else:
            username = from_user['first_name']

        tg_id = from_user['id']

        if tg_id in bakchod_dict:
            a_bakchod = bakchod_dict[tg_id]
        else:
            a_bakchod = bakchod.Bakchod(tg_id, username)

        # Update last seen
        a_bakchod.lastseen = datetime.now()

        # Reward rokda
        a_bakchod.rokda = reward_rokda(a_bakchod.rokda)

        # Backwards compat
        a_bakchod.id = tg_id

        try:
            history = a_bakchod.history
        except:
            a_bakchod.history = {}

        logger.info("Updating Bakchod for username={} rokda={}".format(
            username, 
            a_bakchod.rokda
            ))

        bakchod_dict[tg_id] = a_bakchod

        with open('resources/bakchod.pickle', 'wb') as handle:
            pickle.dump(bakchod_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)


def reward_rokda(r):

        if (r < 0) or r is None:
            r = 0

        # Egalitarian policy - Poor users get more increment than richer users
        r += (100/(r + 10) + 1)
        r = round(r, 2)

        return r


def timesince_query(query_username):

    for bakchod in bakchod_dict.values():
        if bakchod.username == query_username:
            response = timesince_calculator(bakchod.lastseen)
            return(query_username + ' last posted ' + response + ' ago')
    else: 
        return("404")


def timesince_calculator(lastseen):

    now = datetime.now()
    td = now - lastseen
    pretty_td = chaddi_util.pretty_time_delta(td.total_seconds())
    return(pretty_td)


def rokda_query(query_id):

    if query_id in bakchod_dict:
        found_bakchod = bakchod_dict[query_id]
        return("💰" + found_bakchod.username + ' has ' + str(found_bakchod.rokda) + ' ₹okda!')
    else: 
        return("404")


def about_query(query_id):

    if query_id in bakchod_dict:
        found_bakchod = bakchod_dict[query_id]

        about_response = '*About ' + found_bakchod.username + ':* \n'
        about_response = about_response + '~ ID: `{}` \n'.format(found_bakchod.id)
        about_response = about_response + '~ ₹okda: `{}` \n'.format(found_bakchod.rokda)

        try:
            about_response = about_response + '~ Censored: `{}` \n'.format(
                            found_bakchod.censored
                        )
        except:
            about_response = about_response + '~ Censored: `Nope` \n'

        try:
            about_response = about_response + '~ Birthday: `{} {} {}` \n'.format(
                            found_bakchod.birthday.day,
                            found_bakchod.birthday.strftime('%b'),
                            found_bakchod.birthday.year
                        )
        except:
            about_response = about_response + '~ Birthday: `Not set. Please set with /set birthday <your_birthday>` \n'

        return(about_response)
    else: 
        return("404")