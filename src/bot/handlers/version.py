from datetime import datetime
from loguru import logger
from telegram import Update, ParseMode
from src.domain import dc, util
import subprocess

CHADDI_TG_VERSION = "3.0.0"

GIT_COMMIT_ID = (
    subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
    .strip()
    .decode("utf-8")
)

GIT_COMMIT_TIME = datetime.utcfromtimestamp(
    int(
        subprocess.check_output(["git", "show", "-s", "--format=%ct"])
        .strip()
        .decode("utf-8")
    )
)

TIME_BOT_STARTED = datetime.now()


logger.info(
    "[version] parsed GIT_COMMIT_ID={} GIT_COMMIT_TIME={} TIME_BOT_STARTED={}",
    GIT_COMMIT_ID,
    GIT_COMMIT_TIME,
    TIME_BOT_STARTED,
)


def handle(update: Update, context, log_to_dc=True):

    if util.is_admin_tg_user(update.message.from_user):

        if log_to_dc:
            dc.log_command_usage("version", update)

        response = get_chaddi_version()
        logger.info("[version] returning response='{}'", response)

        update.message.reply_text(response, parse_mode=ParseMode.HTML)


def get_chaddi_version():

    now = datetime.now()
    uptime = now - TIME_BOT_STARTED

    response = """
<b>chaddi-tg version {}</b>

<b>Commit ID:</b> {}
<b>Commit Time:</b> {}
<b>Time Started:</b> {}
<b>Uptime:</b> {}
""".format(
        CHADDI_TG_VERSION,
        GIT_COMMIT_ID,
        GIT_COMMIT_TIME,
        TIME_BOT_STARTED,
        util.pretty_time_delta(uptime.seconds),
    )

    return response