#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pickle
import util.logger
import json

# Enable logging
logger = util.logger.get_logger(__name__)

def main():

    try:
        with open('resources/quotes.pickle', 'rb') as handle:
            mPickle = pickle.load(handle)
            logger.info('Loaded Pickle!')
    except:
        logger.info('Pickle not found...')
        return
    
    for i in range(0, len(mPickle)):

        element = mPickle[i]

        try: 
            logger.info(element['id'])
        except:
            logger.info("no id")
            element['id'] = i
    
    try:
        with open('resources/quotes.pickle', 'wb') as handle:
            pickle.dump(mPickle, handle, protocol=pickle.HIGHEST_PROTOCOL)
    except:
        logger.info('Pickle not found...')
        return

if __name__ == "__main__":
    main()