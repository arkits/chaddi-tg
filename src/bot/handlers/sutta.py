import random
from telegram.ext import CallbackContext
from telegram import ParseMode, Update
from loguru import logger
from src.db import Bakchod
from src.domain import dc, util

COMMAND_COST = 200


def handle(update: Update, context: CallbackContext, log_to_dc=True):

    try:

        initiator_user = update.message.from_user
        if initiator_user is None:
            logger.error("[sutta] initiator_user was None!")
            return

        if not util.paywall_user(initiator_user.id, COMMAND_COST):
            update.message.reply_text(
                "Sorry! You don't have enough ₹okda! Each /sutta costs {} ₹okda.".format(
                    COMMAND_COST
                )
            )
            return

        if log_to_dc:
            dc.log_command_usage("sutta", update)

        start_sutta(update, context)

    except Exception as e:
        logger.error("Caught Exception in sutta.handle - e={}", e)


def update_sutta(context: CallbackContext):

    try:

        job = context.job

        chat_id = job.context["chat_id"]
        message_id = job.context["message_id"]
        bakchod_id = job.context["bakchod_id"]

        b = Bakchod.get_by_id(bakchod_id)
        if b is None:
            logger.error("Bakchod not found")
            return

        if b.metadata.get("sutta_ittr") is None:
            b.metadata["sutta_ittr"] = 0
        else:
            b.metadata["sutta_ittr"] += 1
        b.save()

        ittr = b.metadata["sutta_ittr"]

        logger.debug(
            "[sutta] handling update_sutta bakchod_id={} ittr={}", bakchod_id, ittr
        )

        if ittr <= 8:

            cig_start = "(̅_̅_̅_̅(̅_̅"
            cig_end = "_̅()ڪے"
            loop = "_̅"

            looploop = loop * (8 - ittr)

            s = "{}{}{}".format(cig_start, looploop, cig_end)

            context.bot.edit_message_text(s, chat_id, message_id)

        else:
            job.schedule_removal()

            context.bot.edit_message_text("~~~", chat_id, message_id)

            b.metadata["sutta_ittr"] = None
            b.save()

    except Exception as e:
        logger.error("Caught Exception in update_sutta - e={}", e)


def start_sutta(update: Update, context: CallbackContext):

    # Check for previously running sutta jobs
    b = Bakchod.get_by_id(update.message.from_user.id)
    if b is None:
        logger.error("Bakchod not found")
        return

    if b.metadata.get("sutta_ittr") is not None:
        logger.error("[sutta] sutta_ittr was not None...")
        update.message.reply_text(
            "DHUMRAPAN SEHAT KE LIYE HANIKARAK HAI! 💀",
        )
        return

    message = update.message.reply_text(
        "`~~ Ek minute... lighter kidhar hai... ~~`", parse_mode=ParseMode.MARKDOWN_V2
    )

    job_context = {
        "chat_id": message.chat_id,
        "message_id": message.message_id,
        "bakchod_id": update.message.from_user.id,
    }

    job = context.job_queue.run_repeating(
        update_sutta,
        interval=3,
        first=0,
        context=job_context,
    )
