#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pickle
import util.logger
import json
from loguru import logger

def main():

    try:
        with open('resources/bakchod.pickle', 'rb') as handle:
            bakchod_dict = pickle.load(handle)
            logger.info('Loaded Bakchod pickle!')
    except:
        logger.info('Bakchod pickle not found...')
        return
    
    for bakchod in bakchod_dict.values():
        logger.info(bakchod.__dict__)

if __name__ == "__main__":
    main()