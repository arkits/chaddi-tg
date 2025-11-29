import time
import traceback
from openai import OpenAI
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from loguru import logger
from src.domain import config, dc, util

app_config = config.get_config()
client = OpenAI(api_key=app_config.get("OPENAI", "API_KEY"))

MODEL_NAME = "gpt-5-mini"

COMMAND_COST = 200


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        dc.log_command_usage("ask", update)

        if not util.paywall_user(update.effective_user.id, COMMAND_COST):
            await update.message.reply_text(
                f"Sorry! You don't have enough ₹okda! Each `/ask` costs {COMMAND_COST} ₹okda.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        # Extract message
        message = None
        if context.args:
            message = " ".join(context.args)
        elif update.message.reply_to_message:
            if update.message.reply_to_message.text:
                message = update.message.reply_to_message.text
            elif update.message.reply_to_message.caption:
                message = update.message.reply_to_message.caption

        if not message:
            await update.message.reply_text(
                "Please provide a question or reply to a message with `/ask`.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        # Send initial "Thinking..." message
        sent_message = await update.message.reply_text("ek minute...")

        # Stream response from OpenAI
        stream = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": message}],
            stream=True,
        )

        response_text = ""
        last_update_time = 0
        update_interval = 1.0  # seconds

        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                response_text += chunk.choices[0].delta.content

                # Update message periodically to avoid rate limits
                current_time = time.time()
                if current_time - last_update_time > update_interval:
                    try:
                        await sent_message.edit_text(response_text + " ...")
                        last_update_time = current_time
                    except Exception:
                        pass  # Ignore errors during intermediate updates

        # Final update
        await sent_message.edit_text(response_text, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f"Caught Error in ask.handle - {e} \n {traceback.format_exc()}")
        await update.message.reply_text("Something went wrong while asking ChatGPT.")
