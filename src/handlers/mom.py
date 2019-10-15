#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import util
import config
import bakchod_util
import spacy
import json
import random

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Spacy
nlp = spacy.load('en_core_web_sm')

# Handler /mom
# Identify the verb in the sentence
# Make it past tense and add to "v(p) your dad last night"
def handle(bot, update):

    bakchod_util.bakchod_updater(update.message.from_user['username'])
    logger.info("/mom: Handling /mom request from user '%s' in group '%s'", update.message.from_user['username'], update.message.chat.title)

    og_sender = update.message.from_user
    if(og_sender['username']):
        og_sender = "@" + og_sender['username']
    elif(og_sender['firstname']):
        og_sender = og_sender['firstname']

    if update.message.reply_to_message:
        riposte = jokeMom(update.message.reply_to_message.text, og_sender)
        respond_to = update.message.reply_to_message.from_user
    else:
        riposte = jokeMom(update.message.text, og_sender)
    
    if(respond_to['username']):
        respond_to = respond_to['username']
    elif(respond_to['firstname']):
        respond_to = respond_to['firstname']

    mom_response_blacklist = [config.bot_username, "Hirop84"]

    if respond_to not in mom_response_blacklist:
        if update.message.reply_to_message:
            update.message.reply_to_message.reply_text(riposte)
        else:
            update.message.reply_text(riposte)
    else:
        sticker_to_send = 'CAADAQADrAEAAp6M4Ahtgp9JaiLJPxYE'
        update.message.reply_sticker(sticker=sticker_to_send)

# !! SEXISM !!
# make a bad joke about it
def jokeMom(sentence, victim):
    protagonist = "ur mom"

    # flip the joke 20% of times
    if random.random() > 0.8:
        protagonist, victim = victim, protagonist
    
    # extract parts of speech and generate insults
    if sentence is not None:
        verb = getVerb(sentence)
        if verb != 0:
            return "{} {} {} last night ".format(victim, verb, protagonist)
        else:
            adjective = getThisPOS(sentence, 'ADJ')
            if adjective != 0:
                return "{} {} is nice but ur {}".format(victim, protagonist, adjective)
            else:
                propn = getThisPOS(sentence, 'PROPN')
                if propn != 0:
                    return "{} {} {}".format(victim, protagonist, propn)
                else:
                    return "{} should get a life".format(victim)
    else:
        return "{}, please link your aadhaar".format(victim)

# return the first relevant part of speech tag
def getThisPOS(sentence, POS):
    doc = nlp(sentence)
    for token in doc:
        if token.pos_ == POS:
            return token.text
    return 0

# return a random verb from the sentence
def getVerb(sentence):
    doc = nlp(sentence)
    verbs = []
    for token in doc:
        if token.pos_ == 'VERB':
            verbs.append(str(token.lemma_))
    if verbs:
        verbPast = getVerbPast(random.choice(verbs))
        return verbPast
    return 0

# return simple past form of verb
def getVerbPast(verb):
    verbLookupTable = "resources/verbPastLookup.json"
    with open(verbLookupTable) as fp:
        data = json.load(fp)
        try:
            verbPast = data[0][verb]
        except KeyError:
            if verb.endswith('ed'):
                verbPast = verb
            elif verb.endswith('e'):
                verbPast = verb + 'd'
            else:
                verbPast = verb + 'ed'
    return verbPast
