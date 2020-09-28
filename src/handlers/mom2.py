from loguru import logger
from util import util
from domain import metrics
import traceback
import json
import random
from handlers import mom

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

        message = mom.extract_target_message(update)
        if message is None:
            logger.info("[mom2] message was None!")
            return

        response = mom.rake_joke(message, protagonist)

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
