from loguru import logger
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.db import Bakchod
from src.domain import dc, util

COMMAND_COST = 200


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE, log_to_dc=True):
    try:
        initiator_user = update.message.from_user
        if initiator_user is None:
            logger.error("[sutta] initiator_user was None!")
            return

        if not util.paywall_user(initiator_user.id, COMMAND_COST):
            await update.message.reply_text(
                f"Sorry! You don't have enough ₹okda! Each /sutta costs {COMMAND_COST} ₹okda."
            )
            return

        if log_to_dc:
            dc.log_command_usage("sutta", update)

        await start_sutta(update, context)

    except Exception as e:
        logger.error("Caught Exception in sutta.handle - e={}", e)


async def update_sutta(context: ContextTypes.DEFAULT_TYPE):
    try:
        job = context.job

        chat_id = job.data["chat_id"]
        message_id = job.data["message_id"]
        bakchod_id = job.data["bakchod_id"]

        b = Bakchod.get_by_id(bakchod_id)
        if b is None:
            logger.error("Bakchod not found")
            return

        sutta_ittr = util.get_metadata_value(b.metadata, "sutta_ittr")
        if sutta_ittr is None:
            b.metadata = util.set_metadata_value(b.metadata, "sutta_ittr", 0)
        else:
            b.metadata["sutta_ittr"] = sutta_ittr + 1
        b.save()

        ittr = util.get_metadata_value(b.metadata, "sutta_ittr")

        logger.debug("[sutta] handling update_sutta bakchod_id={} ittr={}", bakchod_id, ittr)

        if ittr <= 8:
            cig_start = "(̅_̅_̅_̅(̅_̅"
            cig_end = "_̅()ڪے"
            loop = "_̅"

            looploop = loop * (8 - ittr)

            s = f"{cig_start}{looploop}{cig_end}"

            await context.bot.edit_message_text(s, chat_id, message_id)

        else:
            job.schedule_removal()

            await context.bot.edit_message_text("~~~", chat_id, message_id)

            b.metadata["sutta_ittr"] = None
            b.save()

    except Exception as e:
        logger.error("Caught Exception in update_sutta - e={}", e)


async def start_sutta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    b = Bakchod.get_by_id(update.message.from_user.id)
    if b is None:
        logger.error("Bakchod not found")
        return

    if util.get_metadata_value(b.metadata, "sutta_ittr") is not None:
        logger.error("[sutta] sutta_ittr was not None...")
        await update.message.reply_text(
            "DHUMRAPAN SEHAT KE LIYE HANIKARAK HAI! 💀",
        )
        return

    message = await update.message.reply_text(
        "`~~ Ek minute... lighter kidhar hai... ~~`", parse_mode=ParseMode.MARKDOWN_V2
    )

    job_context = {
        "chat_id": message.chat_id,
        "message_id": message.message_id,
        "bakchod_id": update.message.from_user.id,
    }

    _ = context.job_queue.run_repeating(
        update_sutta,
        interval=3,
        first=0,
        data=job_context,
    )
