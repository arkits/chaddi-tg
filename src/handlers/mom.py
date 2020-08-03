from loguru import logger
from util import util, config
from domain import metrics
from db import dao
import spacy
import json
import random
import datetime
import traceback
from rake_nltk import Rake

chaddi_config = config.get_config()

BOT_USERNAME = "@" + chaddi_config["bot_username"]

mom_response_blacklist = [BOT_USERNAME]

COMMAND_COST = 100

rake = Rake()

preposition_to_verb_map = json.loads(
    open("resources/preposition_to_verb_map.json", "r").read()
)


def handle(update, context):

    try:

        random.seed(datetime.datetime.now())

        util.log_chat("mom", update)

        initiator_id = update.message.from_user["id"]
        if initiator_id is None:
            logger.error("[mom] initiator_id was None!")
            return

        # Check if Bakchod has enough rokda to do a /mom...
        if not util.paywall_user(initiator_id, COMMAND_COST):
            update.message.reply_text(
                "Sorry! You don't have enough ₹okda! Each /mom costs {} ₹okda.".format(
                    COMMAND_COST
                )
            )
            return

        # Extract the protagonist - the protagonist <verb> your <victim> last night
        protagonist = util.extract_pretty_name_from_tg_user(update.message.from_user)

        # Extract the protagonist - user who shall receive the insult
        recipient = extract_recipient(update)
        if recipient is None:
            logger.info("[mom] recipient was None!")
            sticker_to_send = "CAADAQADrAEAAp6M4Ahtgp9JaiLJPxYE"
            update.message.reply_sticker(sticker=sticker_to_send)
            return

        # Check if recipient is in the backlist
        if recipient in mom_response_blacklist:
            if recipient == BOT_USERNAME:
                # Don't insult Chaddi!
                sticker_to_send = "CAADAQADrAEAAp6M4Ahtgp9JaiLJPxYE"
                update.message.reply_sticker(sticker=sticker_to_send)
                return
            else:
                # Protect the users in the blacklist
                update.message.reply_text(
                    recipient + " is protected by a 👁️ Nazar Raksha Kavach"
                )
                return

        # Extract the message for base the insult on
        message = extract_target_message(update)
        if message is None:
            logger.info("[mom] message was None!")
            sticker_to_send = "CAADAQADrAEAAp6M4Ahtgp9JaiLJPxYE"
            update.message.reply_sticker(sticker=sticker_to_send)
            return

        # Generate the response
        if random.random() > 0.50:
            logger.info(
                "[mom] generating response with rake - protagonist={} message={}",
                protagonist,
                message,
            )
            response = rake_joke(message, protagonist)
        else:
            logger.info(
                "[mom] generating response with spacy - protagonist={} message={}",
                protagonist,
                message,
            )
            response = spacy_joke(message, protagonist)

        if random.random() > 0.05:
            if update.message.reply_to_message:
                update.message.reply_to_message.reply_text(response)
            else:
                update.message.reply_text(response)
        else:
            # User has chance to get protected
            update.message.reply_text(
                recipient + " is protected by a 👁️ Nazar Raksha Kavach"
            )

        # Update metrics
        metrics.mom_invoker_counter.labels(user_id=update.message.from_user["id"]).inc()

        return

    except Exception as e:
        logger.error(
            "Caught Error in mom.handle - {} \n {}", e, traceback.format_exc(),
        )
        return


def extract_target_message(update):

    target_message = None

    if update.message.reply_to_message:
        # The invoker invoked the command by replying to a message
        if update.message.reply_to_message.text:
            target_message = update.message.reply_to_message.text

        elif update.message.reply_to_message.caption:
            target_message = update.message.reply_to_message.caption

    else:

        target_message = update.message.text

    return target_message


def extract_recipient(update):
    if update.message.reply_to_message.from_user:
        return util.extract_pretty_name_from_tg_user(
            update.message.reply_to_message.from_user
        )
    else:
        return None


def rake_joke(message, protagonist):

    # Extract a phrase from the message
    rake.extract_keywords_from_text(message)
    phrase = rake.get_ranked_phrases()[0]

    # Extract a random verb from the phrase
    random_verb = extract_random_verb(phrase)

    # Derive a preposition that goes along
    if random_verb in preposition_to_verb_map:
        # This will be an array
        prepositions = preposition_to_verb_map.get(random_verb)
    else:
        prepositions = ["in", "on", "with"]

    # Extract a random preposition
    preposition = random.choice(prepositions)

    return f"{protagonist} {phrase} {preposition} your mom last night"


def spacy_joke(message, protagonist):
    return joke_mom(message, protagonist)


# !! SEXISM !!
# make a bad joke about it
def joke_mom(sentence, protagonist, force=False):

    random.seed(datetime.datetime.now())

    target = "your mom"

    if not force:
        # flip the joke 20% of times
        if random.random() > 0.8:
            target, protagonist = protagonist, target

    # extract parts of speech and generate insults
    if sentence is not None:
        verb = get_verb(sentence)
        if verb != 0:
            return "{} {} {} last night".format(protagonist, verb, target)
        else:
            adjective = get_POS(sentence, "ADJ")
            if adjective != 0:
                return "{} is nice but you are {}".format(protagonist, adjective)
            else:
                propn = get_POS(sentence, "PROPN")
                if propn != 0:
                    past = get_verb_past(propn)
                    return "{} {} {} last night".format(protagonist, past, target)
                else:
                    return random_reply(protagonist)
    else:
        return "{}, please link your aadhaar to continue".format(protagonist)


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


def random_reply(protagonist):

    replies = [
        "{} should get a life".format(protagonist),
        "haaaaaaaaaaaaaaaat",
        "bhaaaaaaaaaaaaaaak",
        "arrey isko hatao re",
        "haat bsdk",
        "bhaak bsdk",
    ]

    random.seed(datetime.datetime.now())
    random_int = random.randint(0, len(replies) - 1)

    return replies[random_int]


# Extracts a random verb from the sentence
def extract_random_verb(sentence):

    doc = util.get_nlp()(sentence)

    verbs = []

    for token in doc:
        if token.pos_ == "VERB":
            verbs.append(str(token.lemma_))

    if len(verbs) > 0:
        return random.choice(verbs)
    else:
        return "played"
