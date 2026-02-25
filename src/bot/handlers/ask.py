import contextlib
import traceback

from loguru import logger
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.db import Group
from src.domain import ai, dc, util

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

        try:
            group = Group.get_by_id(update.effective_chat.id)
            if not group or "ask" not in group.metadata.get("enabled_commands", []):
                logger.info(f"[ask] Command disabled for group {update.effective_chat.id}")
                await update.message.reply_text(
                    "This command is not enabled for this group.",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return
        except Exception as e:
            logger.error(f"[ask] Error checking group permissions: {e}")
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

        # Always use OpenRouter for /ask command
        llm_client = ai.get_openrouter_client()

        # Build messages list
        messages = [{"role": "user", "content": message}]

        # Define callback for streaming updates
        async def update_message(accumulated_text: str):
            with contextlib.suppress(Exception):
                await sent_message.edit_text(accumulated_text + " ...")

        system_prompt = (
            "You are Chaddi, an AI assistant in a Telegram group."
            "You will receive questions from users and you will answer them. "
            "Be helpful, slightly edgy, and engaging. "
            "Keep responses concise and appropriate for a group chat setting."
            "Respond with just the message text in markdown format."
        )

        # Generate response with streaming
        response_text = await llm_client.generate_streaming(
            messages=messages,
            system_prompt=system_prompt,
            on_chunk=update_message,
            update_interval=1.0,
        )

        # Final update
        if not response_text or not response_text.strip():
            response_text = "AI returned an empty response. Please try again."

        try:
            await sent_message.edit_text(response_text, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await sent_message.edit_text(response_text)

    except Exception as e:
        logger.error(f"Caught Error in ask.handle - {e} \n {traceback.format_exc()}")
        await update.message.reply_text("Something went wrong while asking ChatGPT.")
