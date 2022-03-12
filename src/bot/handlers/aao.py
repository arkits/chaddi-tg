from loguru import logger
from telegram import Update
from src.domain import dc, util, config
from telegram import ParseMode
import traceback
from . import mom

app_config = config.get_config()

BOT_USERNAME = app_config.get("TELEGRAM", "BOT_USERNAME")

mom_response_blacklist = [BOT_USERNAME]

COMMAND_COST = 200


def handle(update: Update, context):

    try:

        dc.log_command_usage("aao", update)

        initiator_id = update.message.from_user.id
        if initiator_id is None:
            logger.error("[aao] initiator_id was None!")
            return

        if not util.paywall_user(initiator_id, COMMAND_COST):
            update.message.reply_text(
                "Sorry! You don't have enough ₹okda! Each `/aao` costs {} ₹okda.".format(
                    COMMAND_COST
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        target_message = mom.extract_target_message(update)
        if target_message is None:
            logger.info("[aao] target_message was None!")
            return

        magic_word = extract_magic_word(target_message)
        if magic_word is None:
            logger.info("[aao] magic_word was None!")
            return

        support_word = get_support_word()

        response = "aao {} {}".format(magic_word, support_word)
        response = response.lower()

        logger.info("[aao] generated response={}", response)

        if update.message.reply_to_message:
            update.message.reply_to_message.reply_text(response)
            return
        else:
            update.message.reply_text(response)
            return

    except Exception as e:
        logger.error(
            "Caught Error in aao.handle - {} \n {}",
            e,
            traceback.format_exc(),
        )


def extract_magic_word(target_message):

    doc = util.get_nlp()(target_message)

    # the types on pos that we care about - refer to https://universaldependencies.org/docs/u/pos/
    accepted_pos_types = ["VERB", "NOUN", "PROPN", "ADJ", "ADV"]

    # Create a dict for storing the tokens sorted by pos types
    tokens_sorted = {}
    for pos_type in accepted_pos_types:
        tokens_sorted[pos_type] = []

    for token in doc:

        for pos_type in accepted_pos_types:

            # logger.debug("token={} - pos={}", token, token.pos_)

            if token.pos_ == pos_type:

                if pos_type == "VERB":
                    tokens_sorted[pos_type].append(token.lemma_)
                else:
                    tokens_sorted[pos_type].append(token)

    # remove the key from the dict if it's empty
    # need to use list(), or else python will complain
    for sorted_key in list(tokens_sorted.keys()):
        if len(tokens_sorted[sorted_key]) == 0:
            tokens_sorted.pop(sorted_key, None)

    logger.debug("[aao] tokens_sorted={}", tokens_sorted)

    if len(tokens_sorted.keys()) == 0:
        logger.info("[aao] tokens_sorted.keys() was zero!")
        return None

    # choose which pos_type to use...
    magic_pos_type = util.choose_random_element_from_list(list(tokens_sorted.keys()))
    logger.debug("[aao] magic_pos_type={}", magic_pos_type)

    # choose magic word...
    magic_word = util.choose_random_element_from_list(tokens_sorted[magic_pos_type])

    return magic_word


def get_support_word():

    support_words = ["dikhae", "sikhae", "kare"]

    support_word = util.choose_random_element_from_list(support_words)

    return support_word
