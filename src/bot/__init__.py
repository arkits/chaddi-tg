from loguru import logger
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from src.domain import config, tg_logger, version
from src.domain.scheduler import reschedule_saved_jobs

from . import handlers

app_config = config.get_config()

bot_instance = None


async def post_init(application: Application) -> None:
    """Post initialization callback"""
    global bot_instance
    bot_instance = application.bot
    logger.debug("Setting global bot_instance - bot_instance={}", bot_instance)

    v = version.get_version()

    await tg_logger.log(
        """
*chaddi-tg has started!*

*chaddi-tg version:* `{}`
*Commit ID:* `{}`
*Commit Message:* `{}`
*Commit Time:* `{}`
*Time Started:* `{}`
*Uptime:* `{}`
""".format(
            v["semver"],
            v["git_commit_id"],
            v["git_commit_message"],
            v["git_commit_time"],
            v["time_service_started"],
            v["pretty_uptime"],
        )
    )

    reschedule_saved_jobs(application.job_queue)


def run_telegram_bot():
    # Create the Application and pass it your bot's token.
    application = (
        Application.builder()
        .token(app_config.get("TELEGRAM", "TG_BOT_TOKEN"))
        .post_init(post_init)
        .build()
    )

    # Add command handlers
    application.add_handler(CommandHandler("start", handlers.start.handle))
    application.add_handler(CommandHandler("help", handlers.help.handle))
    application.add_handler(CommandHandler("hi", handlers.hi.handle))
    application.add_handler(CommandHandler("about", handlers.about.handle))
    application.add_handler(CommandHandler("rokda", handlers.rokda.handle))
    application.add_handler(CommandHandler("superpower", handlers.superpower.handle))
    application.add_handler(CommandHandler("gamble", handlers.gamble.handle))
    application.add_handler(CommandHandler("sutta", handlers.sutta.handle))

    application.add_handler(CommandHandler("mom", handlers.mom3.handle))
    application.add_handler(CommandHandler("mom2", handlers.mom2.handle))

    application.add_handler(CommandHandler("set", handlers.setter.handle))
    application.add_handler(CommandHandler("chutiya", handlers.chutiya.handle))
    application.add_handler(CommandHandler("aao", handlers.aao.handle))
    application.add_handler(CommandHandler("daan", handlers.daan.handle))
    application.add_handler(CommandHandler("version", handlers.version.handle))

    application.add_handler(CommandHandler("quote", handlers.quotes.handle))
    application.add_handler(CommandHandler("quotes", handlers.quotes.handle))

    application.add_handler(CommandHandler("roll", handlers.roll.handle))
    application.add_handler(CommandHandler("translate", handlers.translate.handle))
    application.add_handler(CommandHandler("mlai", handlers.mlai.handle))
    application.add_handler(CommandHandler("ocr", handlers.mlai.handle_ocr))
    application.add_handler(CommandHandler("tynm", handlers.tynm.handle))
    application.add_handler(CommandHandler("ytdl", handlers.ytdl.handle))
    application.add_handler(CommandHandler("dalle", handlers.dalle.handle))

    application.add_handler(CommandHandler("remind", handlers.remind.handle))
    application.add_handler(CommandHandler("reminder", handlers.remind.handle))
    application.add_handler(CommandHandler("remindme", handlers.remind.handle))
    application.add_handler(CommandHandler("alarm", handlers.remind.handle))

    # Add message handlers
    application.add_handler(
        MessageHandler(filters.StatusUpdate.ALL, handlers.defaults.status_update)
    )
    application.add_handler(MessageHandler(filters.Document.VIDEO, handlers.webm.handle))
    application.add_handler(MessageHandler(filters.ALL, handlers.defaults.all))

    # Log all errors
    application.add_error_handler(handlers.errors.log_error)

    # Start the Bot
    logger.info("[tg] Starting Telegram Bot with Polling")
    application.run_polling(
        allowed_updates=["message", "edited_message", "channel_post", "edited_channel_post"]
    )


def get_bot_instance():
    global bot_instance
    return bot_instance
