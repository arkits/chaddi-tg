from os import path
from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from src.bot.handlers import mom
from src.domain import dc, util, config
import traceback
from openai import OpenAI


app_config = config.get_config()

BOT_USERNAME = app_config.get("TELEGRAM", "BOT_USERNAME")

mom_response_blacklist = [BOT_USERNAME]

COMMAND_COST = 200

client = OpenAI(api_key=app_config.get("OPENAI", "API_KEY"))

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        dc.log_command_usage("mom3", update)

        initiator_id = update.message.from_user.id
        if initiator_id is None:
            logger.error("[mom3] initiator_id was None!")
            return

        if not util.paywall_user(initiator_id, COMMAND_COST):
            await update.message.reply_text(
                "Sorry! You don't have enough ₹okda! Each `/mom3` costs {} ₹okda.".format(
                    COMMAND_COST
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        protagonist = util.extract_pretty_name_from_tg_user(update.message.from_user)

        message = mom.extract_target_message(update)
        if message is None:
            logger.info("[mom3] message was None!")
            return

        instructions = open(
            path.join(util.RESOURCES_DIR, "openai", "mom3-prompt.txt"), "r"
        ).read()


        input = "User({}): {}".format(protagonist, message[:1000])
        input += "\nResponse: "

        logger.debug("[mom3] prompt={} \n {}", instructions, input)

        response = client.responses.create(
            model="gpt-5-mini",
            instructions=instructions,
            input=input
        )

        output_text = response.output_text.strip()

        logger.info("[mom3] openai response='{}'", output_text)

        response = output_text

        if update.message.reply_to_message:
            await update.message.reply_to_message.reply_text(response)
            return
        else:
            await update.message.reply_text(response)
            return

    except Exception as e:
        logger.error(
            "Caught Error in mom.handle - {} \n {}",
            e,
            traceback.format_exc(),
        )
        return
