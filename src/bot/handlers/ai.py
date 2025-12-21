import time
import traceback

from loguru import logger
from openai import OpenAI
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.db import Group
from src.domain import config, dc, util

app_config = config.get_config()

# AI Provider configuration
AI_PROVIDER = app_config.get("AI", "PROVIDER", fallback="openai")  # "openai" or "gemini"

# OpenAI setup
openai_client = None
if AI_PROVIDER == "openai" or app_config.has_option("OPENAI", "API_KEY"):
    openai_client = OpenAI(api_key=app_config.get("OPENAI", "API_KEY"))

# Gemini setup
gemini_client = None
if AI_PROVIDER == "gemini" or app_config.has_option("GEMINI", "API_KEY"):
    try:
        from google import genai

        gemini_client = genai.Client(api_key=app_config.get("GEMINI", "API_KEY"))
    except Exception as e:
        logger.warning(f"[ai] Failed to initialize Gemini client: {e}")

# Model names
OPENAI_MODEL = app_config.get("AI", "OPENAI_MODEL", fallback="gpt-5-mini-2025-08-07")
GEMINI_MODEL = app_config.get("AI", "GEMINI_MODEL", fallback="gemini-2.5-flash")

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

        # Route to appropriate provider
        if AI_PROVIDER == "gemini":
            response_text = await _handle_gemini(message_text, image_bytes, image_mime_type)
        else:
            response_text = await _handle_openai(message_text, image_bytes, sent_message)

        # Final update
        try:
            await sent_message.edit_text(response_text, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            # If markdown parsing fails, send without formatting
            await sent_message.edit_text(response_text)

    except Exception as e:
        logger.error(f"Caught Error in ai.handle - {e} \n {traceback.format_exc()}")
        await update.message.reply_text("Something went wrong while processing your request.")


async def _handle_openai(message_text: str, image_bytes: bytes | None, sent_message) -> str:
    """Handle request using OpenAI API"""
    if openai_client is None:
        return "OpenAI client is not configured."

    # Build content for the message
    content = []

    if image_bytes:
        import base64

        base64_image = base64.b64encode(bytes(image_bytes)).decode("utf-8")
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
            }
        )

    content.append({"type": "text", "text": message_text})

    # Stream response from OpenAI
    stream = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": content}],
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

    return response_text


async def _handle_gemini(
    message_text: str, image_bytes: bytes | None, image_mime_type: str | None
) -> str:
    """Handle request using Google Gemini API"""
    if gemini_client is None:
        return "Gemini client is not configured."

    from google.genai import types

    # Build contents for the request
    contents = []

    if image_bytes:
        # Add image as inline data
        contents.append(
            types.Part.from_bytes(
                data=bytes(image_bytes),
                mime_type=image_mime_type or "image/jpeg",
            )
        )

    # Add text prompt
    contents.append(message_text)

    # Generate response
    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
    )

    return response.text
