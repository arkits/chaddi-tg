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
logger = logging.getLogger(__name__)

# Load Spacy
nlp = spacy.load('en_core_web_sm')

mom_response_blacklist = [config.bot_username, "Hirop84"]


# Handler /mom
# Identify the verb in the sentence
# Make it past tense and add to "v(p) your dad last night"
def handle(bot, update):

    # Update Bakchod pickle
    # bakchod_util.bakchod_updater(update.message.from_user)
    
    logger.info("/mom: Handling /mom request from user '%s' in group '%s'", update.message.from_user['username'], update.message.chat.title)

    # Get Telegram user id
    og_sender_id = update.message.from_user['id']

    # Check if Bakchod has enough rokda to do a /mom...
    if checkIfUserCanRiposte(og_sender_id):

        # Get sender's name
        og_sender_name = update.message.from_user
        if(og_sender_name['username']):
            og_sender_name = "@" + og_sender_name['username']
        elif(og_sender_name['firstname']):
            og_sender_name = og_sender_name['firstname']

        # Get recipient's name
        if update.message.reply_to_message:
            riposte = jokeMom(update.message.reply_to_message.text, og_sender_name)
            respond_to = update.message.reply_to_message.from_user        
            if(respond_to['username']):
                respond_to = respond_to['username']
            elif(respond_to['firstname']):
                respond_to = respond_to['firstname']
        else:
            riposte = jokeMom(update.message.text, og_sender_name)
            respond_to = og_sender_name

        if respond_to not in mom_response_blacklist:
            if random.random() > 0.05:
                if update.message.reply_to_message:
                    update.message.reply_to_message.reply_text(riposte)
                else:
                    update.message.reply_text(riposte)
            else:
                update.message.reply_text("@" + respond_to + " is protected by a 👁️ Nazar Raksha Kavach")
        elif respond_to == config.bot_username:
            sticker_to_send = 'CAADAQADrAEAAp6M4Ahtgp9JaiLJPxYE'
            update.message.reply_sticker(sticker=sticker_to_send)
        else:
            update.message.reply_text("@" + respond_to + " is protected by a 👁️ Nazar Raksha Kavach")
    
    else:
        # Bakchod doesn't have enough rokda :(
        update.message.reply_text("Sorry! You don't have enough ₹okda! Each /mom costs 50 ₹okda.")


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


# Check whether a user can initate a /mom. 
# Also subtracts 50 rokda.
def checkIfUserCanRiposte(tg_id):

    a_bakchod = bakchod_util.get_bakchod(tg_id)

    if a_bakchod.rokda <= 50:
        return False
    else:
        a_bakchod.rokda = a_bakchod.rokda - 50
        bakchod_util.set_bakchod(a_bakchod)
        return True
