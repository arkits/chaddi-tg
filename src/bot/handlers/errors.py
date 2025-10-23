from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes
import traceback
from src.domain import tg_logger


async def log_error(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update:
        return

    logger.error(
        "Caught Fatal Error! error={} \n \nupdate={} \n \ncontext={} \n \ntraceback={}",
        context.error,
        update.to_json() if update else "No update",
        context.__dict__,
        traceback.format_exc(),
    )

    tg_logger.log(
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
