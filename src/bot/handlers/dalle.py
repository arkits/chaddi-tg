from os import path
import uuid
from loguru import logger
from telegram import Update
from src.bot.handlers import mom
from src.db import Bakchod, bakchod_dao
from src.domain import dc, util, config
from telegram import ParseMode
import traceback
import openai


app_config = config.get_config()

COMMAND_ENABLED = True
COMMAND_COST = 500

openai.api_key = app_config.get("OPENAI", "API_KEY")


def handle(update: Update, context):

    try:

        dc.log_command_usage("dalle", update)

        initiator_id = update.message.from_user.id
        if initiator_id is None:
            logger.error("[dalle] initiator_id was None!")
            return

        if not util.paywall_user(initiator_id, COMMAND_COST):
            update.message.reply_text(
                "Sorry! You don't have enough ₹okda! Each `/dalle` costs {} ₹okda.".format(
                    COMMAND_COST
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        b = bakchod_dao.get_or_create_bakchod_from_tg_user(update.message.from_user)

        if "dalle" in b.metadata and b.metadata["dalle"] == True:
            pass
        else:
            logger.info("[dalle] denied request for disabled bakchod={}", b.pretty_name)
            update.message.reply_text(
                "/dalle is not enabled for you. Ping @arkits with your TG ID - {}".format(
                    b.tg_id
                )
            )
            return

        try:

            prompt = extract_prompt(update)
            if prompt is None or prompt == "":
                logger.info("[dalle] message was None!")
                update.message.reply_text("HAAAAAAAATTTTT")
                return

            logger.info("[dalle] prompt={}", prompt)

            if COMMAND_ENABLED:

                response = openai.Image.create(prompt=prompt, n=1, size="256x256")
                image_url = response["data"][0]["url"]

                logger.info(
                    "[dalle] generated image_url={} prompt='{}'", image_url, prompt
                )

                resource_path = util.acquire_external_resource(
                    image_url, "dalle_{}".format(uuid.uuid4())
                )

                with open(resource_path, "rb") as photo_to_upload:
                    logger.info("[dalle] uploading completed photo")
                    update.message.reply_photo(photo=photo_to_upload, caption=prompt)

                util.delete_file(resource_path)

                return

            else:
                update.message.reply_text(
                    "/dalle temporarily disabled, try again later... maybe PAYUPP!!!?????"
                )
                return

        except Exception as e:
            logger.error(
                "Caught Error in generation - {} \n {}",
                e,
                traceback.format_exc(),
            )
            update.message.reply_text(
                "Something has gone wrong! Ping @arkits about this XD"
            )

        return

    except Exception as e:
        logger.error(
            "Caught Error in mom.handle - {} \n {}",
            e,
            traceback.format_exc(),
        )
        return


def extract_prompt(update: Update):

    prompt = None

    if update.message.text:
        prompt = update.message.text

    prompt = prompt.split("/dalle ")[1]

    return prompt
