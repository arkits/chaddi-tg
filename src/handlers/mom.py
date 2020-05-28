from loguru import logger
from util import util, config
from db import dao
import spacy
import json
import random
import datetime
import traceback

chaddi_config = config.get_config()

BOT_USERNAME = "@" + chaddi_config["bot_username"]

mom_response_blacklist = [BOT_USERNAME]


def handle(update, context):

    try:

        random.seed(datetime.datetime.now())

        util.log_chat("mom", update)

        # Get Telegram user id
        og_sender_id = update.message.from_user["id"]

        # Check if Bakchod has enough rokda to do a /mom...
        if util.paywall_user(og_sender_id, 100):

            # Get sender's name
            og_sender_name = util.extract_pretty_name_from_tg_user(
                update.message.from_user
            )

            # Get recipient's name
            if update.message.reply_to_message:
                riposte = joke_mom(update.message.reply_to_message.text, og_sender_name)
                respond_to = util.extract_pretty_name_from_tg_user(
                    update.message.reply_to_message.from_user
                )
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
                    update.message.reply_text(
                        respond_to + " is protected by a 👁️ Nazar Raksha Kavach"
                    )
            else:
                if respond_to == BOT_USERNAME:
                    # Don't insult Chaddi!
                    sticker_to_send = "CAADAQADrAEAAp6M4Ahtgp9JaiLJPxYE"
                    update.message.reply_sticker(sticker=sticker_to_send)
                else:
                    # Protect the users in the blacklist
                    update.message.reply_text(
                        respond_to + " is protected by a 👁️ Nazar Raksha Kavach"
                    )

        else:
            # Bakchod doesn't have enough rokda :(
            update.message.reply_text(
                "Sorry! You don't have enough ₹okda! Each /mom costs 50 ₹okda."
            )

    except Exception as e:
        logger.error(
            "Caught Error in mom.handle - {} \n {}", e, traceback.format_exc(),
        )


# !! SEXISM !!
# make a bad joke about it
def joke_mom(sentence, victim, force=False):

    random.seed(datetime.datetime.now())

    protagonist = "your mom"

    if not force:
        # flip the joke 20% of times
        if random.random() > 0.8:
            protagonist, victim = victim, protagonist

    # extract parts of speech and generate insults
    if sentence is not None:
        verb = get_verb(sentence)
        if verb != 0:
            return "{} {} {} last night".format(victim, verb, protagonist)
        else:
            adjective = get_POS(sentence, "ADJ")
            if adjective != 0:
                return "{} is nice but you are {}".format(victim, adjective)
            else:
                propn = get_POS(sentence, "PROPN")
                if propn != 0:
                    past = get_verb_past(propn)
                    return "{} {} {} last night".format(victim, past, protagonist)
                else:
                    return random_reply(victim)
    else:
        return "{}, please link your aadhaar to continue".format(victim)


# return the first relevant part of speech tag
def get_POS(sentence, POS):

    doc = util.get_nlp()(sentence)
    for token in doc:
        if token.pos_ == POS:
            return token.text
    return 0


# return a random verb from the sentence
def get_verb(sentence):

    doc = util.get_nlp()(sentence)

    verbs = []

    for token in doc:
        if token.pos_ == "VERB":
            verbs.append(str(token.lemma_))

    if verbs:

        verbPast = get_verb_past(random.choice(verbs))
        return verbPast

    else:

        noun = get_POS(sentence, "NOUN")

        if noun:

            # see if the noun has a verb form
            verb_form_past = get_verb_past(noun)

            if verb_form_past != -1:
                return verb_form_past

    return 0


# return simple past form of verb
def get_verb_past(verb):

    verbLookupTable = util.get_verbLookupTable()

    try:
        verbPast = verbLookupTable[0][verb]
    except KeyError:
        if verb.endswith("ed"):
            verbPast = verb
        elif verb.endswith("e"):
            verbPast = verb + "d"
        else:
            verbPast = verb + "ed"

    return verbPast


def random_reply(victim):

    replies = [
        "{} should get a life".format(victim),
        "haaaaaaaaaaaaaaaat",
        "bhaaaaaaaaaaaaaaak",
        "arrey isko hatao re",
        "haat bsdk",
        "bhaak bsdk",
    ]

    random.seed(datetime.datetime.now())
    random_int = random.randint(0, len(replies) - 1)

    return replies[random_int]
