from loguru import logger
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
)
import handlers
from util import config


app_config = config.get_config()


def run_telegram_bot():
    # Create the Updater and pass it your bot's token.
    updater = Updater(app_config.get("TELEGRAM", "TG_BOT_TOKEN"))

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", handlers.basics.start))
    dispatcher.add_handler(CommandHandler("help", handlers.basics.help_command))

    dispatcher.add_handler(MessageHandler(Filters.all, handlers.basics.all))

    # Start the Bot
    logger.info("Starting Telegram Bot with Polling")
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()