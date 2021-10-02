from loguru import logger
from src import bot
from src.domain import config
from telegram import ParseMode
import traceback

app_config = config.get_config()
LOGGING_CHAT_ID = app_config.get("TELEGRAM", "LOGGING_CHAT_ID")


def log(message: str):

    try:

        bot_instance = bot.get_bot_instance()
        if bot_instance is None:
            raise Exception("Failed to get_bot_instance")

        bot_instance.send_message(
            chat_id=LOGGING_CHAT_ID, text=message[:4096], parse_mode=ParseMode.MARKDOWN
        )

    except Exception as e:

        logger.error(
            "Caught error in tg_logger.log. e={} traceback={}",
            e,
            traceback.format_exc(),
        )
