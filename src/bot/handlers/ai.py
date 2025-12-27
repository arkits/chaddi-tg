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
        dc.log_command_usage("ai", update)

        if not util.paywall_user(update.effective_user.id, COMMAND_COST):
            await update.message.reply_text(
                f"Sorry! You don't have enough ₹okda! Each `/ai` costs {COMMAND_COST} ₹okda.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        try:
            group = Group.get_by_id(update.effective_chat.id)
            if not group or "ai" not in group.metadata.get("enabled_commands", []):
                logger.info(f"[ai] Command disabled for group {update.effective_chat.id}")
                await update.message.reply_text(
                    "This command is not enabled for this group.",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return
        except Exception as e:
            logger.error(f"[ai] Error checking group permissions: {e}")
            return

        # Extract message text and image
        message_text = None
        image_bytes = None
        image_mime_type = None

        # Check for text in command args
        if context.args:
            message_text = " ".join(context.args)

        # Check for reply to message
        reply_message = update.message.reply_to_message
        if reply_message:
            # Get text from reply
            if not message_text:
                if reply_message.text:
                    message_text = reply_message.text
                elif reply_message.caption:
                    message_text = reply_message.caption

            # Get photo from reply
            if reply_message.photo:
                # Get the largest photo (last in the list)
                photo = reply_message.photo[-1]
                photo_file = await photo.get_file()
                image_bytes = await photo_file.download_as_bytearray()
                image_mime_type = "image/jpeg"
                logger.info(f"[ai] Downloaded photo from reply, size={len(image_bytes)} bytes")

        # Check for photo in the current message
        if update.message.photo:
            photo = update.message.photo[-1]
            photo_file = await photo.get_file()
            image_bytes = await photo_file.download_as_bytearray()
            image_mime_type = "image/jpeg"
            logger.info(f"[ai] Downloaded photo from message, size={len(image_bytes)} bytes")
            # Use caption as message text if no args provided
            if not message_text and update.message.caption:
                # Remove the /ai command from caption
                caption = update.message.caption
                message_text = caption[3:].strip() if caption.startswith("/ai") else caption

        if not message_text and not image_bytes:
            await update.message.reply_text(
                "Please provide a question, reply to a message, or send an image with `/ai`.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        # Default prompt for image-only requests
        if image_bytes and not message_text:
            message_text = "Describe this image."

        # Send initial "Thinking..." message
        sent_message = await update.message.reply_text("ek minute...")

        # Use the unified LLM client
        llm_client = ai.get_default_client()

        # Define callback for streaming updates
        async def update_message(accumulated_text: str):
            with contextlib.suppress(Exception):
                await sent_message.edit_text(accumulated_text + " ...")

        # Generate response with streaming
        response_text = await llm_client.generate_streaming(
            message_text=message_text,
            image_bytes=image_bytes,
            image_mime_type=image_mime_type,
            on_chunk=update_message,
            update_interval=1.0,
        )

        # Final update
        try:
            await sent_message.edit_text(response_text, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            # If markdown parsing fails, send without formatting
            await sent_message.edit_text(response_text)

    except Exception as e:
        logger.error(f"Caught Error in ai.handle - {e} \n {traceback.format_exc()}")
        await update.message.reply_text("Something went wrong while processing your request.")
