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
bot_username = "@" + config.bot_username
mom_response_blacklist = [bot_username, "@Hirop84"]


# Handler /mom
# Identify the verb in the sentence
# Make it past tense and add to "v(p) your dad last night"
def handle(bot, update):
    
    logger.info("/mom: Handling /mom request from user '%s' in group '%s'", update.message.from_user['username'], update.message.chat.title)

    # Get Telegram user id
    og_sender_id = update.message.from_user['id']

    # Check if Bakchod has enough rokda to do a /mom...
    if check_if_user_can_riposte(og_sender_id):

        # Get sender's name
        og_sender_name = extract_pretty_name(update.message.from_user)

        # Get recipient's name
        if update.message.reply_to_message:
            riposte = joke_mom(update.message.reply_to_message.text, og_sender_name)
            respond_to = extract_pretty_name(update.message.reply_to_message.from_user)
        else:
            riposte = joke_mom(update.message.text, og_sender_name)
            respond_to = og_sender_name

        if respond_to not in mom_response_blacklist:
            if random.random() > 0.10:
                if update.message.reply_to_message:
                    update.message.reply_to_message.reply_text(riposte)
                else:
                    update.message.reply_text(riposte)
            else:
                # User has chance to get protected
                update.message.reply_text(respond_to + " is protected by a 👁️ Nazar Raksha Kavach")
        else:
            if respond_to == bot_username:
                # Don't insult Chaddi!
                sticker_to_send = 'CAADAQADrAEAAp6M4Ahtgp9JaiLJPxYE'
                update.message.reply_sticker(sticker=sticker_to_send)
            else:
                # Protect the users in the blacklist
                update.message.reply_text(respond_to + " is protected by a 👁️ Nazar Raksha Kavach")
    
    else:
        # Bakchod doesn't have enough rokda :(
        update.message.reply_text("Sorry! You don't have enough ₹okda! Each /mom costs 50 ₹okda.")

def extract_pretty_name(from_user):

    if(from_user['username']):
        from_user = "@" + from_user['username']
    elif(from_user['firstname']):
        from_user = from_user['firstname']

    return from_user

# !! SEXISM !!
# make a bad joke about it
def joke_mom(sentence, victim):
    protagonist = "Your mom"

    # flip the joke 20% of times
    if random.random() > 0.8:
        protagonist, victim = victim, protagonist
    
    # extract parts of speech and generate insults
    if sentence is not None:
        verb = get_verb(sentence)
        if verb != 0:
            return "{} {} {} last night ".format(victim, verb, protagonist)
        else:
            adjective = get_POS(sentence, 'ADJ')
            if adjective != 0:
                return "{} is nice but you are {}".format(victim, adjective)
            else:
                propn = get_POS(sentence, 'PROPN')
                if propn != 0:
                    return "{} {} {}".format(victim, protagonist, propn)
                else:
                    return "{} should get a life".format(victim)
    else:
        return "{}, please link your aadhaar to continue".format(victim)


# return the first relevant part of speech tag
def get_POS(sentence, POS):
    doc = nlp(sentence)
    for token in doc:
        if token.pos_ == POS:
            return token.text
    return 0


# return a random verb from the sentence
def get_verb(sentence):
    doc = nlp(sentence)
    verbs = []
    for token in doc:
        if token.pos_ == 'VERB':
            verbs.append(str(token.lemma_))
    if verbs:
        verbPast = get_verb_past(random.choice(verbs))
        return verbPast
    else:
        noun = get_POS(sentence, 'NOUN')
        # see if the noun has a verb form
        verb_form_past = get_verb_past(noun, lemmatize_unknown_verbs = FALSE)
        if verb_form_past != -1:
            return verb_form_past
    return 0


# return simple past form of verb
def get_verb_past(verb, lemmatize_unknown_verbs = True):
    verbLookupTable = "resources/verbPastLookup.json"
    with open(verbLookupTable) as fp:
        data = json.load(fp)
        try:
            verbPast = data[0][verb]
        except KeyError:
            if lemmatize_unknown_verbs:
                if verb.endswith('ed'):
                    verbPast = verb
                elif verb.endswith('e'):
                    verbPast = verb + 'd'
                else:
                    verbPast = verb + 'ed'
            else:
                verbPast = -1
    return verbPast


# Check whether a user can initate a /mom. 
# Also subtracts 50 rokda.
def check_if_user_can_riposte(tg_id):
    a_bakchod = bakchod_util.get_bakchod(tg_id)

    if a_bakchod.rokda <= 50:
        return False
    else:
        a_bakchod.rokda = a_bakchod.rokda - 50
        bakchod_util.set_bakchod(a_bakchod)
        return True
