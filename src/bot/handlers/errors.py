import traceback

from loguru import logger
from telegram import Update
from telegram.error import BadRequest, Forbidden
from telegram.ext import ContextTypes

from src.domain import analytics, tg_logger

# BadRequest messages Telegram returns when the bot can't post in a chat
# (muted, restricted, or no longer a member). Nothing we can do about these.
CANT_SEND_MESSAGES = (
    "not enough rights",
    "have no rights to send",
    "chat_write_forbidden",
    "chat not found",
)


def is_cant_send_error(error: Exception | None) -> bool:
    if isinstance(error, Forbidden):
        return True
    if isinstance(error, BadRequest):
        message = error.message.lower()
        return any(m in message for m in CANT_SEND_MESSAGES)
    return False


async def log_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update:
        return

    if is_cant_send_error(context.error):
        chat = update.effective_chat if isinstance(update, Update) else None
        logger.warning(
            "Can't send messages to chat_id={} title={}: {}",
            chat.id if chat else None,
            chat.title if chat else None,
            context.error,
        )
        return

    user = update.effective_user if isinstance(update, Update) else None
    chat = update.effective_chat if isinstance(update, Update) else None
    analytics.capture_exception(
        context.error,
        distinct_id=str(user.id) if user else None,
        properties={
            "source": "telegram",
            "chat_id": str(chat.id) if chat else None,
            "chat_type": chat.type if chat else None,
            "chat_title": chat.title if chat else None,
            "username": user.username if user else None,
        },
    )

    logger.error(
        "Caught Fatal Error! error={} \n \nupdate={} \n \ncontext={} \n \ntraceback={}",
        context.error,
        update.to_json() if update else "No update",
        context.__dict__,
        traceback.format_exc(),
    )

    await tg_logger.log(
        """
*⚠️ A fatal error was caught!*

Error: `{}`

Update:
`{}`

Traceback:
`{}`
""".format(
            context.error,
            update.to_json() if update else "No update",
            traceback.format_exc(),
        )
    )

    return
