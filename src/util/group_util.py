#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pickle
import random
from datetime import datetime, date, timezone

import util.logger
from models import group

# Enable logging
logger = util.logger.get_logger(__name__)

# Using Python pickling for data persistence
try:
    with open('resources/group.pickle', 'rb') as handle:
        groups_dict = pickle.load(handle)
        logger.info('Loaded Group pickle')
except:
    logger.info('Group pickle not found... Making new one')
    groups_dict = {}
    with open('resources/group.pickle', 'wb') as handle:
        pickle.dump(groups_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

# Update Groups based on chat and from_user
def group_updater(chat, from_user):

    if get_group(chat['id']) is None:
        g = group.Group(chat['id'], chat['title'])
    else:
        g = get_group(chat['id'])

    if from_user['id'] not in g.members:
        g.members.append(from_user['id'])

    update_group(g)


# Get a Group based on tg_id
def get_group(tg_id):

    if tg_id in groups_dict:
        group = groups_dict[tg_id]
    else:
        group = None

    return group


# Update Group and commit to pickle
def update_group(a_group):

    groups_dict[a_group.id] = a_group

    with open('resources/group.pickle', 'wb') as handle:
        pickle.dump(groups_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)