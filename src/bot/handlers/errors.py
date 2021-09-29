from loguru import logger
from telegram import Update
from telegram.ext import CallbackContext
import traceback
from src.domain import tg_logger


def log_error(update: Update, context: CallbackContext):
    logger.error(
        "Caught Fatal Error! error={} \n \nupdate={} \n \ncontext={} \n \ntraceback={}",
        context.error,
        update.to_json(),
        context.__dict__,
        traceback.format_exc(),
    )

    tg_logger.log(
        "Caught Fatal Error! `error={}` \n \n`traceback={}`".format(
            context.error,
            traceback.format_exc(),
        )
    )

    return