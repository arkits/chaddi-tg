from loguru import logger
from util import util
import traceback


def handle(update, context):

    try:

        util.log_chat("purge", update)

        end_message_id = update.message.message_id

        if not util.is_admin(update.message.from_user["id"]):
            safe_delete_message(context.bot, end_message_id, update.message.chat_id)
            return

        start_message_id = extract_start_message_id(update)
        if start_message_id is None:
            logger.info("[purge] end_message_id was None!")
            return

        logger.info(
            "[purge] start_message_id={} end_message_id={}",
            start_message_id,
            end_message_id,
        )

        for purge_message_id in range(start_message_id, end_message_id):
            logger.debug(
                "[purge] deleting message_id={} group_id={}",
                purge_message_id,
                update.message.chat_id,
            )
            break_the_loop = safe_delete_message(
                context.bot, purge_message_id, update.message.chat_id
            )

            if break_the_loop:
                break

    except Exception as e:
        logger.error(
            "Caught Error in default.handle - {} \n {}", e, traceback.format_exc(),
        )


def extract_start_message_id(update):

    target_message_id = None

    if update.message.reply_to_message:
        target_message_id = update.message.reply_to_message.message_id

    return target_message_id


def safe_delete_message(bot, message_id, chat_id):

    break_the_loop = False

    try:
        bot.delete_message(
            chat_id=chat_id, message_id=message_id,
        )
    except Exception as e:
        logger.error(
            "Caught Error in purge handler's delete loop - {} \n {}",
            e,
            traceback.format_exc(),
        )
        bot.send_message(
            chat_id=chat_id,
            text="Looks like I'm not able to delete messages... Please check the Group permissions!",
        )
        break_the_loop = True

    return break_the_loop
