#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pickle
import util.logger
import json
from loguru import logger

# reward_rokda_to_all.py
# As part of New Years 2020, Rewards all users extra 1000 Rokda.


def main():

    try:
        with open('resources/bakchod.pickle', 'rb') as handle:
            bakchod_dict = pickle.load(handle)
            logger.info('Loaded Bakchod pickle!')
    except:
        logger.info('Bakchod pickle not found...')
        return
    
    for bakchod_key in bakchod_dict.keys():

        bakchod = bakchod_dict[bakchod_key]

        old_rokda = bakchod.rokda

        new_rokda = int(old_rokda + 1000)

        bakchod.rokda = new_rokda

        bakchod_dict[bakchod_key] = bakchod

        logger.info("Rewarded {}. old_rokda={}, new_rokda={}", bakchod.username, old_rokda, new_rokda)

    try:
        with open('resources/bakchod.pickle', 'wb') as handle:
            pickle.dump(bakchod_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
    except:
        logger.info('Pickle not found...')
        return

if __name__ == "__main__":
    main()