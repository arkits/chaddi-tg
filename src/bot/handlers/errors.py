from loguru import logger
from telegram import Update
from telegram.ext import CallbackContext
import traceback


def log_error(update: Update, context: CallbackContext):
    logger.error(
        "Caught Fatal Error! error={} \n \nupdate={} \n \ncontext={} \n \ntraceback={}",
        context.error,
        update.to_json(),
        context.__dict__,
        traceback.format_exc(),
    )
    return