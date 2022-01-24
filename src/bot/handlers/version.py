from loguru import logger
from telegram import Update, ParseMode
from src.domain import dc, util, version


def handle(update: Update, context, log_to_dc=True):

    if util.is_admin_tg_user(update.message.from_user):

        if log_to_dc:
            dc.log_command_usage("version", update)

        response = get_chaddi_version()
        logger.info("[version] returning response='{}'", response)

        update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)


def get_chaddi_version():

    v = version.get_version()

    response = """
*chaddi-tg version:* {}
*Commit ID:* {}
*Commit Message:* {}
*Commit Time:* {}
*Time Started:* {}
*Uptime:* {}
""".format(
        v["semver"],
        v["git_commit_id"],
        v["git_commit_message"],
        v["git_commit_time"],
        v["time_service_started"],
        v["pretty_uptime"],
    )

    return response
