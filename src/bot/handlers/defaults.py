import random
import traceback
from datetime import datetime

from loguru import logger
from peewee import DoesNotExist
from telegram import Update
from telegram.ext import ContextTypes

from src.bot.handlers import mom_spacy, roll
from src.db import EMPTY_JSON, Bakchod, GroupMember, bakchod_dao, group_dao
from src.domain import config, dc, rokda, util

from . import ai, antiwordle, bestie, hi, instagram, musiclinks, x_links

app_config = config.get_config()

# Config values are sometimes quoted - normalize to a bare lowercase username
BOT_USERNAME = app_config.get("TELEGRAM", "BOT_USERNAME").strip().strip("\"'").lstrip("@").lower()


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

    await handle_bot_mention(update, context)

    await antiwordle.handle(update, context)

    await musiclinks.handle(update, context)

    await x_links.handle(update, context)

    await instagram.handle(update, context)


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
                rm = util.get_metadata_value(bakchod.metadata, key)

                for route_message_props in rm:
                    if str(route_message_props["to_group"]) == str(update.message.chat_id):
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

                if (
                    group_id is not None
                    and censored_metadata
                    and group_id in censored_metadata.get("group_ids", [])
                ):
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

                if (
                    group_id is not None
                    and auto_mom_metadata
                    and group_id in auto_mom_metadata.get("group_ids", [])
                    and random.random() > 0.5
                ):
                    logger.info(
                        "[metadata] auto_mom - victim={} message={}",
                        util.extract_pretty_name_from_bakchod(bakchod),
                        update.message.text,
                    )

                    response = mom_spacy.joke_mom(update.message.text, "Chaddi", True)

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


def extract_bot_mention_question(message, bot_username: str | None = None) -> str | None:
    """
    Check if the bot was @mentioned in a message, and if so return the message
    text with the mention removed - ie. the question being asked of the bot.

    Returns None if the bot wasn't mentioned. Returns an empty string if it was
    mentioned with nothing else (eg. a bare "@ChaddiBot").
    """
    bot_username = bot_username or BOT_USERNAME

    text = message.text or message.caption
    if not text:
        return None

    entities = message.entities or message.caption_entities
    if not entities:
        return None

    for entity in entities:
        mention_text = None

        if entity.type == "mention":
            # Parse via the Message helper - entity offsets are in UTF-16 units
            parsed = (
                message.parse_entity(entity)
                if message.text
                else message.parse_caption_entity(entity)
            )
            if parsed.lstrip("@").lower() == bot_username:
                mention_text = parsed
        elif entity.type == "text_mention" and entity.user is not None:
            username = entity.user.username
            if username and username.lower() == bot_username:
                mention_text = (
                    message.parse_entity(entity)
                    if message.text
                    else message.parse_caption_entity(entity)
                )

        if mention_text is not None:
            return text.replace(mention_text, "", 1).strip()

    return None


async def handle_bot_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Route messages that @mention the bot to the AI handler.

    The mention is stripped out and the rest of the message becomes the
    question. Replies are handled by ai.handle, so mentioning the bot while
    replying to a message asks about that message.
    """
    try:
        message = update.message

        if message.from_user is not None and message.from_user.is_bot:
            return

        # Prefer the username Telegram reports over the configured one - a stale
        # BOT_USERNAME would otherwise make mentions silently stop working
        bot_username = getattr(context.bot, "username", None)
        if isinstance(bot_username, str) and bot_username:
            bot_username = bot_username.lstrip("@").lower()
        else:
            bot_username = BOT_USERNAME

        question = extract_bot_mention_question(message, bot_username)
        if question is None:
            return

        logger.info(f"[defaults] Bot mentioned, routing to ai - question='{question}'")

        await ai.handle(update, context, question=question or None, quiet=True)
    except Exception as e:
        logger.error("Caught Exception in handle_bot_mention - e={}", e)

    return


async def handle_dice_rolls(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dice = update.message.dice

    if dice is None:
        return

    if dice.emoji == "🎲":
        await roll.handle_dice_rolls(dice.value, update, context)

    return


async def status_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Handle both message and edited_message updates
    message = update.message or update.edited_message
    if message is None:
        logger.warning("[status_update] Update has no message or edited_message")
        return

    g = group_dao.get_group_from_update(update)

    # Handle new_chat_member
    new_chat_members = message.new_chat_members

    if new_chat_members is not None:
        for new_member in new_chat_members:
            b = bakchod_dao.get_or_create_bakchod_from_tg_user(new_member)

            try:
                GroupMember.get(
                    (GroupMember.group_id == g.group_id) & (GroupMember.bakchod_id == b.tg_id)
                )
            except DoesNotExist:
                logger.info(
                    "[status_update] bakchod={} has joined group={}",
                    b.tg_id,
                    g.group_id,
                )

                GroupMember.create(group=g, bakchod=b)

    # Handle left_chat_member
    left_chat_member = message.left_chat_member

    if left_chat_member is not None:
        b = bakchod_dao.get_or_create_bakchod_from_tg_user(left_chat_member)

        logger.info("[status_update] bakchod={} has left group={}", b.tg_id, g.group_id)

        GroupMember.delete().where(
            (GroupMember.group_id == g.group_id) & (GroupMember.bakchod_id == b.tg_id)
        ).execute()
