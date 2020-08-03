from loguru import logger
from util import util
from domain import metrics
import traceback
from rake_nltk import Rake
import json
import random


rake = Rake()

preposition_to_verb_map = json.loads(
    open("resources/preposition_to_verb_map.json", "r").read()
)

COMMAND_COST = 200


def handle(update, context):

    try:

        util.log_chat("mom2", update)

        initiator_id = update.message.from_user["id"]
        if initiator_id is None:
            logger.error("[mom2] initiator_id was None!")
            return

        if not util.paywall_user(initiator_id, COMMAND_COST):
            update.message.reply_text(
                "Sorry! You don't have enough ₹okda! Each /mom2 costs {} ₹okda.".format(
                    COMMAND_COST
                )
            )
            return

        metrics.mom2_invoker_counter.labels(
            user_id=update.message.from_user["id"]
        ).inc()

        protagonist = util.extract_pretty_name_from_tg_user(update.message.from_user)

        message = extract_target_message(update)
        if message is None:
            logger.info("[mom2] message was None!")
            return

        response = generate_mom_joke(protagonist, message)

        logger.info("[mom2] generated response={}", response)

        if update.message.reply_to_message:
            update.message.reply_to_message.reply_text(response)
            metrics.mom2_victim_counter.labels(
                user_id=update.message.reply_to_message.from_user["id"]
            ).inc()
            return
        else:
            update.message.reply_text(response)
            return

    except Exception as e:
        logger.error(
            "Caught Error in mom2.handle - {} \n {}", e, traceback.format_exc(),
        )


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


def generate_mom_joke(protagonist, message):

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
