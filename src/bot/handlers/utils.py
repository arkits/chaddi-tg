import traceback
from collections.abc import Callable
from functools import wraps

from loguru import logger
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.domain import dc, util


def log_command_with_error_handler(command_name: str):
    """
    Decorator to handle logging and error handling for command handlers.
    """

    def decorator(handler_func: Callable):
        @wraps(handler_func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            try:
                dc.log_command_usage(command_name, update)
                return await handler_func(update, context, *args, **kwargs)
            except Exception as e:
                logger.error(
                    f"Caught Error in {command_name}.handle - {e} \n {traceback.format_exc()}"
                )
                await update.message.reply_text("Something went wrong!")
                return

        return wrapper

    return decorator


def extract_command_from_text(text: str) -> str | None:
    """
    Extract the command from the message text (second word after command).
    Returns None if no second word found.
    """
    try:
        query = text.lower().split(" ")
        return query[1]
    except Exception:
        return None


def extract_query_params(text: str) -> list[str]:
    """
    Extract all parameters from command text as a list.
    Returns empty list if parsing fails.
    """
    try:
        return text.split(" ")
    except Exception:
        return []


async def check_admin_and_reply(update: Update) -> bool:
    """
    Check if user is admin and reply with standard error message if not.
    Returns True if admin, False otherwise.
    """
    if not util.is_admin_tg_user(update.message.from_user):
        await update.message.reply_text("Chal kat re bsdk!")
        return False
    return True


async def check_paywall_and_reply(
    update: Update, user_id: int, cost: int, command_name: str
) -> bool:
    """
    Check if user has enough rokda and reply with standard error message if not.
    Returns True if payment successful, False otherwise.
    """
    if not util.paywall_user(user_id, cost):
        await update.message.reply_text(
            f"Sorry! You don't have enough ₹okda! Each `/{command_name}` costs {cost} ₹okda.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return False
    return True


async def reply_with_error(
    update: Update, error_message: str, parse_mode: ParseMode = ParseMode.MARKDOWN
) -> None:
    """
    Send an error message reply with specified parse mode.
    """
    await update.message.reply_text(text=error_message, parse_mode=parse_mode)


async def extract_receiver_bakchod(update: Update, query_params: list[str], param_index: int = 1):
    """
    Extract receiver bakchod from update (reply to message or username).
    Returns Bakchod or None.
    """
    from src.db import bakchod_dao

    receiver = None

    if update.message.reply_to_message:
        receiver = bakchod_dao.get_or_create_bakchod_from_tg_user(
            update.message.reply_to_message.from_user
        )
    else:
        if update.message.entities:
            for entity in update.message.entities:
                if entity.type == "text_mention" and entity.user is not None:
                    receiver = bakchod_dao.get_or_create_bakchod_from_tg_user(entity.user)

        if receiver is None:
            receiver_username = query_params[param_index]
            if receiver_username.startswith("@"):
                receiver_username = receiver_username[1:]
            receiver = bakchod_dao.get_bakchod_by_username(receiver_username)

    return receiver


def extract_message_text_or_caption(update: Update) -> str | None:
    """
    Extract text or caption from a message.
    Returns text if available, otherwise caption, otherwise None.
    """
    if hasattr(update.message, "text") and update.message.text:
        return update.message.text
    if hasattr(update.message, "caption") and update.message.caption:
        return update.message.caption
    return None
