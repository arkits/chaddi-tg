#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pickle
import util.logger
import json
import uuid 

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

    mDict = {}
    
    for i in range(0, len(mPickle)):
        
        element = mPickle[i]

        quote_id = uuid.uuid1().int

        element['id'] = quote_id

        mDict[quote_id] = element
    
    try:
        with open('resources/quotes.pickle', 'wb') as handle:
            pickle.dump(mDict, handle, protocol=pickle.HIGHEST_PROTOCOL)
    except:
        logger.info('Pickle not found...')
        return

if __name__ == "__main__":
    main()