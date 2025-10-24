import traceback
from os import path

from loguru import logger
from openai import OpenAI
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.bot.handlers import mom_spacy
from src.domain import config, dc, util

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
                f"Sorry! You don't have enough ₹okda! Each `/mom` costs {COMMAND_COST} ₹okda.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        protagonist = util.extract_pretty_name_from_tg_user(update.message.from_user)

        message = mom_spacy.extract_target_message(update)
        if message is None:
            logger.info("[mom3] message was None!")
            return

        # Send immediate response
        if update.message.reply_to_message:
            sent_message = await update.message.reply_to_message.reply_text("٩(◕‿◕｡)۶ generating response...")
        else:
            sent_message = await update.message.reply_text("generating response...")

        instructions = open(path.join(util.RESOURCES_DIR, "openai", "mom3-prompt.txt")).read()

        input = f"User({protagonist}): {message[:1000]}"
        input += "\nResponse: "

        logger.debug("[mom3] prompt={} \n {}", instructions, input)

        # Generate multiple jokes
        num_jokes = 4
        jokes = []

        logger.info("[mom3] generating {} jokes...", num_jokes)

        for i in range(num_jokes):
            response = client.responses.create(
                model="gpt-5-mini", instructions=instructions, input=input
            )
            joke = response.output_text.strip()
            jokes.append(joke)
            logger.info("[mom3] joke {}: '{}'", i + 1, joke)

        # Now have LLM pick the funniest one
        logger.info("[mom3] asking LLM to pick the funniest joke...")
        await sent_message.edit_text("(o´▽`o) generating clap back...")

        selection_prompt = "You are a comedy expert. From the following mom jokes, pick the funniest one. Only return the joke itself, nothing else.\n\n"
        for i, joke in enumerate(jokes, 1):
            selection_prompt += f"Joke {i}: {joke}\n\n"

        logger.debug("[mom3] selection prompt: {}", selection_prompt)

        selection_response = client.responses.create(
            model="gpt-5-mini",
            instructions="You are a comedy expert evaluating jokes. Pick the funniest joke and return ONLY that joke, word for word, with no additional commentary.",
            input=selection_prompt
        )

        output_text = selection_response.output_text.strip()

        logger.info("[mom3] selected joke: '{}'", output_text)

        response = output_text

        # Edit the sent message with the actual response
        await sent_message.edit_text(response)
        return

    except Exception as e:
        logger.error(
            "Caught Error in mom.handle - {} \n {}",
            e,
            traceback.format_exc(),
        )
        return
