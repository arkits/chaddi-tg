import contextlib
import traceback

from loguru import logger
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.db import Group, Message
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

        # Build conversation history for group chats
        conversation_history = ""
        is_group = update.message.chat.type in ("group", "supergroup")
        current_user_name = util.extract_pretty_name_from_tg_user(update.message.from_user)

        if is_group:
            conversation_history = _build_conversation_history(
                group_id=str(update.message.chat.id),
                limit=20,
                current_user_name=current_user_name,
                current_message=message_text,
            )
            if conversation_history:
                logger.info(
                    f"[ai] Built conversation history with {len(conversation_history)} chars for group {update.message.chat.id}"
                )

        # Send initial "Thinking..." message
        sent_message = await update.message.reply_text("ek minute...")

        # Use the unified LLM client
        llm_client = ai.get_default_client()

        # Use conversation history if available, otherwise use just the message text
        full_message = conversation_history if conversation_history else message_text

        # Define callback for streaming updates
        async def update_message(accumulated_text: str):
            with contextlib.suppress(Exception):
                await sent_message.edit_text(accumulated_text + " ...")

        # Generate response with streaming
        response_text = await llm_client.generate_streaming(
            message_text=full_message,
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


def _build_conversation_history(
    group_id: str,
    limit: int = 20,
    current_user_name: str | None = None,
    current_message: str | None = None,
) -> str:
    """
    Build conversation history from the last N messages in a group.

    Args:
        group_id: The group ID to fetch messages from
        limit: Number of messages to include (default: 20)
        current_user_name: Name of the current user asking the question
        current_message: The current message text

    Returns:
        Formatted conversation history string with context, or empty string if no messages found
    """
    try:
        # Fetch last N messages from the database, ordered by time (oldest first for context)
        messages = (
            Message.select()
            .where(Message.to_id == group_id)
            .where(Message.text.is_null(False))  # Only include messages with text
            .order_by(Message.time_sent.desc())
            .limit(limit)
        )

        if not messages:
            # If no history, just return the current message
            if current_message:
                return current_message
            return ""

        # Reverse to get chronological order (oldest first)
        messages_list = list(messages)
        messages_list.reverse()

        # Build conversation history
        history_parts = []
        for msg in messages_list:
            if msg.text and msg.from_bakchod:
                bakchod_name = util.extract_pretty_name_from_bakchod(msg.from_bakchod)
                if bakchod_name:
                    # Format: "Name: message text"
                    history_parts.append(f"{bakchod_name}: {msg.text}")

        if not history_parts:
            # If no valid history parts, just return the current message
            if current_message:
                return current_message
            return ""

        # Build the full conversation context
        conversation_context = "\n".join(history_parts)

        # Add the current message if provided
        if current_message and current_user_name:
            conversation_context += f"\n{current_user_name}: {current_message}"
        elif current_message:
            conversation_context += f"\n{current_message}"

        return conversation_context

    except Exception as e:
        logger.warning(f"[ai] Error building conversation history: {e}")
        # Fallback to just the current message
        if current_message:
            return current_message
        return ""
