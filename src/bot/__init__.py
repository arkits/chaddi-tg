from loguru import logger
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
)
from . import handlers
from src.domain import config
from src.domain import tg_logger
from src.domain import version

app_config = config.get_config()

bot_instance = None


def run_telegram_bot():

    # Create the Updater and pass it your bot's token.
    updater = Updater(app_config.get("TELEGRAM", "TG_BOT_TOKEN"))

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", handlers.start.handle))
    dispatcher.add_handler(CommandHandler("help", handlers.help.handle))
    dispatcher.add_handler(CommandHandler("hi", handlers.hi.handle))
    dispatcher.add_handler(CommandHandler("about", handlers.about.handle))
    dispatcher.add_handler(CommandHandler("rokda", handlers.rokda.handle))
    dispatcher.add_handler(CommandHandler("superpower", handlers.superpower.handle))
    dispatcher.add_handler(CommandHandler("gamble", handlers.gamble.handle))
    dispatcher.add_handler(CommandHandler("mom", handlers.mom.handle))
    dispatcher.add_handler(CommandHandler("mom2", handlers.mom2.handle))
    dispatcher.add_handler(CommandHandler("set", handlers.setter.handle))
    dispatcher.add_handler(CommandHandler("chutiya", handlers.chutiya.handle))
    dispatcher.add_handler(CommandHandler("aao", handlers.aao.handle))
    dispatcher.add_handler(CommandHandler("daan", handlers.daan.handle))
    dispatcher.add_handler(CommandHandler("version", handlers.version.handle))
    dispatcher.add_handler(CommandHandler("quote", handlers.quotes.handle))
    dispatcher.add_handler(CommandHandler("quotes", handlers.quotes.handle))
    dispatcher.add_handler(CommandHandler("roll", handlers.roll.handle))
    dispatcher.add_handler(CommandHandler("translate", handlers.translate.handle))
    dispatcher.add_handler(CommandHandler("mlai", handlers.mlai.handle))
    dispatcher.add_handler(CommandHandler("ocr", handlers.mlai.handle_ocr))

    dispatcher.add_handler(
        MessageHandler(Filters.status_update, handlers.defaults.status_update)
    )
    dispatcher.add_handler(
        MessageHandler(Filters.document.category("video"), handlers.webm.handle)
    )
    dispatcher.add_handler(MessageHandler(Filters.all, handlers.defaults.all))

    # Log all errors
    dispatcher.add_error_handler(handlers.errors.log_error)

    # Start the Bot
    logger.info("[tg] Starting Telegram Bot with Polling")
    updater.start_polling()

    global bot_instance
    bot_instance = updater.bot
    logger.debug("Setting global bot_instance - bot_instance={}", bot_instance)

    v = version.get_version()

    tg_logger.log(
        """
*chaddi-tg has started!*

*Commit ID:* {}
""".format(
            v["git_commit_id"]
        )
    )

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


def get_bot_instance():
    global bot_instance
    return bot_instance