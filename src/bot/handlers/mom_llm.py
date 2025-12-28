import traceback
from os import path

from loguru import logger
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.bot.handlers import mom_spacy
from src.domain import ai, config, dc, util

app_config = config.get_config()

BOT_USERNAME = app_config.get("TELEGRAM", "BOT_USERNAME")

mom_response_blacklist = [BOT_USERNAME]

COMMAND_COST = 200

MODEL_NAME = "gpt-5"


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
            sent_message = await update.message.reply_to_message.reply_text(
                "٩(◕‿◕｡)۶ generating zoke..."
            )
        else:
            sent_message = await update.message.reply_text("generating zoke...")

        with open(path.join(util.RESOURCES_DIR, "openai", "mom3-prompt.txt")) as f:
            instructions = f.read()

        input = f"User({protagonist}): {message[:1000]}"
        input += "\nResponse: "

        # Generate multiple jokes in one request
        num_jokes = 4

        logger.info("[mom3] generating {} jokes in one request...", num_jokes)

        multi_joke_instructions = (
            instructions
            + f"\n\nGenerate exactly {num_jokes} different variations of your response. Format your output as:\n1. [first joke]\n2. [second joke]\n3. [third joke]\n4. [fourth joke]"
        )

        logger.debug("[mom3] prompt={} \n {} \n {}", instructions, input, multi_joke_instructions)

        # Use LLMClient wrapper
        llm_client = ai.get_openai_client(model=MODEL_NAME)
        llm_response = await llm_client.generate(
            message_text=f"{multi_joke_instructions}\n\n{input}",
        )

        # Parse the jokes from the response
        output = llm_response.text.strip()
        logger.debug("[mom3] raw response: '{}'", output)

        # Extract jokes from numbered list
        jokes = []
        lines = output.split("\n")
        for line in lines:
            line = line.strip()
            # Match lines starting with "1.", "2.", etc.
            if line and len(line) > 3 and line[0].isdigit() and line[1:3] in [". ", ".)"]:
                joke = line[3:].strip() if line[2] == " " else line[2:].strip()
                jokes.append(joke)
                logger.info("[mom3] joke {}: '{}'", len(jokes), joke)

        # Fallback: if parsing failed, try splitting by double newlines
        if len(jokes) < num_jokes:
            logger.warning(
                "[mom3] Failed to parse {} jokes from numbered list, trying fallback parsing",
                num_jokes,
            )
            jokes = [j.strip() for j in output.split("\n\n") if j.strip()][:num_jokes]
            for i, joke in enumerate(jokes, 1):
                logger.info("[mom3] fallback joke {}: '{}'", i, joke)

        # Final fallback: use the whole response if we still don't have enough jokes
        if len(jokes) == 0:
            logger.warning("[mom3] Could not parse jokes, using entire response")
            jokes = [output]

        # Now have LLM pick the funniest one
        logger.info("[mom3] asking LLM to pick the funniest joke...")
        await sent_message.edit_text("(o`▽`o) curating clap back...")

        selection_prompt = "You are a comedy expert. From the following mom jokes, pick the funniest one. Only return the joke itself, nothing else.\n\n"
        for i, joke in enumerate(jokes, 1):
            selection_prompt += f"Joke {i}: {joke}\n\n"

        logger.debug("[mom3] selection prompt: {}", selection_prompt)

        # Use LLMClient wrapper (reuse same client)
        selection_response = await llm_client.generate(
            message_text=f"You are a comedy expert evaluating jokes. Pick the funniest joke and return ONLY that joke, word for word, with no additional commentary.\n\n{selection_prompt}",
        )

        output_text = selection_response.text.strip()

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
