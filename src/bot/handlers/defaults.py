import random
import traceback
from datetime import datetime

from loguru import logger
from peewee import DoesNotExist
from telegram import Update
from telegram.ext import ContextTypes

from src.bot.handlers import mom_spacy, roll
from src.db import EMPTY_JSON, Bakchod, GroupMember, bakchod_dao, group_dao
from src.domain import dc, rokda, util

from . import antiwordle, bestie, hi, musiclinks


async def all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    dc.sync_persistence_data(update)

    # If the update was related to a message send from a user...
    if hasattr(update.message, "from_user"):
        from_user = update.message.from_user
    else:
        logger.debug("[all] update had no message.from_user... fast failing")
        return

    # Reward rokda to Bakchod
    b = bakchod_dao.get_or_create_bakchod_from_tg_user(from_user)
    b.rokda = rokda.reward_rokda(b.rokda)
    b.updated = datetime.now()
    b.save()

    await handle_bakchod_metadata_effects(update, context, b)

    await handle_dice_rolls(update, context)

    await handle_message_matching(update, context)

    await antiwordle.handle(update, context)

    await musiclinks.handle(update, context)


async def handle_bakchod_metadata_effects(
    update: Update, context: ContextTypes.DEFAULT_TYPE, bakchod: Bakchod
):
    if bakchod.metadata is None:
        return

    if bakchod.metadata == EMPTY_JSON:
        return

    group_id = util.get_group_id_from_update(update)

    bot = context.bot

    try:
        for key in bakchod.metadata:
            if key == "route-messages":
                rm = bakchod.metadata[key]

                # logger.debug("route-messages metadata was set - {}", rm)

                for route_message_props in rm:
                    # if the message is posted to the same group, then ignore it
                    if str(route_message_props["to_group"]) == str(
                        update.message.chat_id
                    ):
                        logger.trace(
                            "[metadata] route-messages - posted in the same group - {} // {}",
                            route_message_props["to_group"],
                            update.message.chat_id,
                        )

                        continue

                    await context.bot.forward_message(
                        chat_id=route_message_props["to_group"],
                        from_chat_id=update.message.chat_id,
                        message_id=update.message.message_id,
                    )

            if key == "censored":
                censored_metadata = bakchod.metadata[key]

                if group_id is not None and group_id in censored_metadata["group_ids"]:
                    logger.info(
                        "[metadata] censoring {}",
                        util.extract_pretty_name_from_bakchod(bakchod),
                    )

                    try:
                        await bot.delete_message(
                            chat_id=update.message.chat_id,
                            message_id=update.message.message_id,
                        )
                    except Exception as e:
                        logger.error(
                            "Caught Error in censoring Bakchod - {} \n {}",
                            e,
                            traceback.format_exc(),
                        )
                        await bot.send_message(
                            chat_id=update.message.chat_id,
                            text="Looks like I'm not able to delete messages... Please check the Group permissions!",
                        )

                    return

            if key == "auto_mom":
                auto_mom_metadata = bakchod.metadata[key]

                if group_id is not None and group_id in auto_mom_metadata["group_ids"]:
                    if random.random() > 0.5:
                        logger.info(
                            "[metadata] auto_mom - victim={} message={}",
                            util.extract_pretty_name_from_bakchod(bakchod),
                            update.message.text,
                        )

                        response = mom_spacy.joke_mom(
                            update.message.text, "Chaddi", True
                        )

                        await update.message.reply_text(response)
                        return

    except Exception as e:
        logger.error("Caught Exception in handle_bakchod_metadata_effects - e={}", e)

    return


async def handle_message_matching(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text

    if message_text is not None:
        # Handle 'hi' messages
        if message_text.lower() == "hi":
            await hi.handle(update, context, log_to_dc=False)

        # Handle bestie messages
        if "bestie" in message_text.lower():
            await bestie.handle(update, context, log_to_dc=False)

    return


async def handle_dice_rolls(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dice = update.message.dice

    if dice is None:
        return

    if dice.emoji == "🎲":
        await roll.handle_dice_rolls(dice.value, update, context)

    return


async def status_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    g = group_dao.get_group_from_update(update)

    # Handle new_chat_member
    new_chat_members = update.message.new_chat_members

    if new_chat_members is not None:
        for new_member in new_chat_members:
            b = bakchod_dao.get_or_create_bakchod_from_tg_user(new_member)

            try:
                GroupMember.get(
                    (GroupMember.group_id == g.group_id)
                    & (GroupMember.bakchod_id == b.tg_id)
                )
            except DoesNotExist:
                logger.info(
                    "[status_update] bakchod={} has joined group={}",
                    b.tg_id,
                    g.group_id,
                )

                GroupMember.create(group=g, bakchod=b)

    # Handle left_chat_member
    left_chat_member = update.message.left_chat_member

    if left_chat_member is not None:
        b = bakchod_dao.get_or_create_bakchod_from_tg_user(left_chat_member)

        logger.info("[status_update] bakchod={} has left group={}", b.tg_id, g.group_id)

        GroupMember.delete().where(
            (GroupMember.group_id == g.group_id) & (GroupMember.bakchod_id == b.tg_id)
        ).execute()
