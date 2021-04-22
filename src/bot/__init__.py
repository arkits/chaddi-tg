from loguru import logger
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
)
from . import handlers
from domain import config


app_config = config.get_config()


def run_telegram_bot():
    # Create the Updater and pass it your bot's token.
    updater = Updater(app_config.get("TELEGRAM", "TG_BOT_TOKEN"))

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", handlers.start.handle))
    dispatcher.add_handler(CommandHandler("help", handlers.help.handle))
    dispatcher.add_handler(CommandHandler("hi", handlers.hi.handle))
    dispatcher.add_handler(CommandHandler("about", handlers.about.handle))
    dispatcher.add_handler(CommandHandler("rokda", handlers.rokda.handle))

    dispatcher.add_handler(MessageHandler(Filters.status_update, handlers.defaults.status_update))
    dispatcher.add_handler(MessageHandler(Filters.document.category("video"), handlers.webm.handle))
    dispatcher.add_handler(MessageHandler(Filters.all, handlers.defaults.all))

    # Log all errors
    dispatcher.add_error_handler(handlers.errors.log_error)

    # Start the Bot
    logger.info("[tg] Starting Telegram Bot with Polling")
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()