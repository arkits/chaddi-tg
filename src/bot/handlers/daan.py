import math
from src.db import bakchod_dao
from loguru import logger
from telegram import Update
from src.domain import dc, util, config
from telegram import ParseMode
import traceback

app_config = config.get_config()

BOT_USERNAME = app_config.get("TELEGRAM", "BOT_USERNAME")

mom_response_blacklist = [BOT_USERNAME]

COMMAND_COST = 200


def handle(update: Update, context):

    try:

        dc.log_command_usage("daan", update)

        # Extract query...
        query = update.message.text
        query = query.split(" ")

        if len(query) < 2:
            update.message.reply_text(
                text="Haat chutiya! Syntax is `/daan @username 786`",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        # Extract Sender
        sender = bakchod_dao.get_or_create_bakchod_from_tg_user(
            update.message.from_user
        )

        # Extract Receiver
        receiver = None

        if update.message.reply_to_message:
            # Request is a reply to message... Extract receiver from ID
            receiver = bakchod_dao.get_or_create_bakchod_from_tg_user(
                update.message.reply_to_message.from_user
            )

            # Donation can be the rest of the message
            donation = query[1:]

        else:
            # Request includes the username as a mention
            if update.message.entities:
                for entity in update.message.entities:
                    if entity.type == "text_mention" and entity.user is not None:
                        receiver = bakchod_dao.get_or_create_bakchod_from_tg_user(
                            update.entity.user.id
                        )

            # Last attempt... try to lookup username in DB
            if receiver is None:

                receiver_username = query[1]

                # Remove the "@" prefix
                if receiver_username.startswith("@"):
                    receiver_username = receiver_username[1:]

                # TODO: implement this...
                # receiver = dao.get_bakchod_by_username(receiver_username)

            # Donation can be the rest of the message
            donation = query[2:]

        # Handle if receiver could be extracted
        if receiver is None:
            if receiver_username:
                update.message.reply_text(receiver_username + "??? Who dat???")
                return
            else:
                update.message.reply_text("Kisko daan do be????")
                return

        # Parse Daan amount
        try:
            daan = float("".join(donation))
            daan = round(daan, 2)
            daan = abs(daan)
        except Exception as e:
            update.message.reply_text("Kitna ₹okda be???")
            return

        if not math.isfinite(daan):
            update.message.reply_text(
                "Yeh dekho chutiyapa chal ra hai. Setting {}'s rokda to 0!".format(
                    util.extract_pretty_name_from_bakchod(sender)
                )
            )
            sender.rokda = 0
            sender.save()
            return

        logger.info(
            "[daan] sender={} receiver={} daan={}",
            util.extract_pretty_name_from_bakchod(sender),
            util.extract_pretty_name_from_bakchod(receiver),
            daan,
        )

        # Checking if sender has enough rokda
        sender_rokda = sender.rokda
        if (sender_rokda - daan) < 0:
            update.message.reply_text("Gareeb saale! You don't have enough ₹okda!")
            return

        # Sender is trying to daan to themselves... :thinking_face:
        if sender.tg_id == receiver.tg_id:
            logger.info(
                "[daan] Sender is trying to daan to themselves... :thinking_face:"
            )
            file_id = "CAADAwADrQADnozgCI_qxocBgD_OFgQ"
            sticker_to_send = file_id
            update.message.reply_sticker(sticker=sticker_to_send)
            return

        # Commit Daan transaction to DB
        sender_rokda_pre_tx = sender.rokda
        sender.rokda = sender.rokda - daan
        sender.save()

        receiver_rokda_pre_tx = receiver.rokda
        receiver.rokda = receiver.rokda + daan
        receiver.save()

        logger.info(
            "[daan] commit daan tx - sender_rokda_pre_tx={} sender.rokda={} receiver_rokda_pre_tx={} receiver.rokda={}",
            sender_rokda_pre_tx,
            sender.rokda,
            receiver_rokda_pre_tx,
            receiver.rokda,
        )

        response = "{} gave {} 🤲 a daan of {} ₹okda! 🎉 ".format(
            util.extract_pretty_name_from_bakchod(sender),
            util.extract_pretty_name_from_bakchod(receiver),
            daan,
        )

        logger.info("[daan] returning response='{}'", response)

        update.message.reply_text(response)

    except Exception as e:
        logger.error(
            "Caught Error in daan.handle - {} \n {}",
            e,
            traceback.format_exc(),
        )
        return