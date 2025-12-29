import contextlib
import traceback

from loguru import logger
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.db import CommandUsage, Group
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
        user_question = None
        if context.args:
            user_question = " ".join(context.args)

        # Check for reply to message
        reply_message = update.message.reply_to_message
        reply_context_parts = []

        if reply_message:
            # Extract text and caption from reply message
            if reply_message.text:
                reply_context_parts.append(reply_message.text)
            if reply_message.caption:
                reply_context_parts.append(reply_message.caption)

            # Get photo from reply (prioritize reply image over current message image)
            if reply_message.photo:
                # Get the largest photo (last in the list)
                photo = reply_message.photo[-1]
                photo_file = await photo.get_file()
                image_bytes = await photo_file.download_as_bytearray()
                image_mime_type = "image/jpeg"
                logger.info(f"[ai] Downloaded photo from reply, size={len(image_bytes)} bytes")

            # Combine reply context parts
            if reply_context_parts:
                reply_context = "\n".join(reply_context_parts)
                # If user provided a question, combine it with reply context
                if user_question:
                    message_text = f"{reply_context}\n\n{user_question}"
                else:
                    message_text = reply_context

        # Check for photo in the current message (only if no image from reply)
        if not image_bytes and update.message.photo:
            photo = update.message.photo[-1]
            photo_file = await photo.get_file()
            image_bytes = await photo_file.download_as_bytearray()
            image_mime_type = "image/jpeg"
            logger.info(f"[ai] Downloaded photo from message, size={len(image_bytes)} bytes")

        # Use caption from current message if no text yet
        if not message_text and update.message.caption:
            # Remove the /ai command from caption
            caption = update.message.caption
            message_text = caption[3:].strip() if caption.startswith("/ai") else caption

        # Use user question if no reply context was found
        if not message_text and user_question:
            message_text = user_question

        if not message_text and not image_bytes:
            await update.message.reply_text(
                "Please provide a question, reply to a message, or send an image with `/ai`.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        # Default prompt for image-only requests
        if image_bytes and not message_text:
            message_text = "Describe this image."

        # Format message with username
        username = util.extract_pretty_name_from_tg_user(update.message.from_user)
        formatted_message = f"{username}: {message_text}"

        # Build conversation history for group chats
        is_group = update.message.chat.type in ("group", "supergroup")

        # Send initial "Thinking..." message
        sent_message = await update.message.reply_text("ek minute...")

        # Use the unified LLM client
        llm_client = ai.get_default_client()

        # Build messages list with conversation history for group chats
        messages = []
        if is_group:
            messages = _build_ai_conversation_messages(
                group_id=str(update.message.chat.id),
                limit=20,
                current_user_message=formatted_message,
            )
            if messages:
                logger.info(
                    f"[ai] Built conversation with {len(messages)} messages for group {update.message.chat.id}"
                )

        # If no conversation history, use single message
        if not messages:
            messages = [{"role": "user", "content": formatted_message}]

        # Define callback for streaming updates
        async def update_message(accumulated_text: str):
            with contextlib.suppress(Exception):
                await sent_message.edit_text(accumulated_text + " ...")

        # System prompt for the AI assistant
        system_prompt = (
            "You are Chaddi, an AI assistant in a Telegram group. You will receive messages from users and you will respond to them. "
            "Be helpful, slightly edgy, and engaging. "
            "Keep responses concise and appropriate for a group chat setting."
        )

        # Generate response with streaming
        response_text = await llm_client.generate_streaming(
            messages=messages,
            system_prompt=system_prompt,
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

        # Save the conversation to CommandUsage metadata
        try:
            _save_ai_conversation(update, formatted_message, response_text)
        except Exception as e:
            logger.warning(f"[ai] Failed to save conversation: {e}")

    except Exception as e:
        logger.error(f"Caught Error in ai.handle - {e} \n {traceback.format_exc()}")
        await update.message.reply_text("Something went wrong while processing your request.")


def _save_ai_conversation(update: Update, user_message: str, bot_response: str):
    """
    Save the AI conversation to CommandUsage metadata.

    Args:
        update: The Telegram update
        user_message: The user's message
        bot_response: The bot's response
    """
    try:
        from src.db import Bakchod

        bakchod = Bakchod.get(Bakchod.tg_id == update.message.from_user.id)
        group = Group.get_by_id(update.message.chat.id)

        # Find the most recent CommandUsage for "ai" command (should be the one just created)
        # We look for one created in the last minute to ensure we get the right one
        from datetime import datetime, timedelta

        recent_time = datetime.now() - timedelta(minutes=1)
        command_usage = (
            CommandUsage.select()
            .where(CommandUsage.command_name == "ai")
            .where(CommandUsage.from_bakchod == bakchod)
            .where(CommandUsage.group == group)
            .where(CommandUsage.executed_at >= recent_time)
            .order_by(CommandUsage.executed_at.desc())
            .limit(1)
            .first()
        )

        if command_usage:
            # Update metadata with conversation
            if command_usage.metadata is None:
                command_usage.metadata = {}
            command_usage.metadata["user_message"] = user_message
            command_usage.metadata["bot_response"] = bot_response
            command_usage.save()
            logger.debug(f"[ai] Saved conversation to CommandUsage {command_usage.id}")
        else:
            logger.warning("[ai] Could not find recent CommandUsage to save conversation")
    except Exception as e:
        logger.warning(f"[ai] Error saving conversation: {e}")


def _build_ai_conversation_messages(
    group_id: str, limit: int = 20, current_user_message: str | None = None
) -> list[dict[str, str]]:
    """
    Build conversation messages list from the last N /ai command invocations.

    Args:
        group_id: The group ID to fetch conversations from
        limit: Number of conversations to include (default: 20)
        current_user_message: The current user's message

    Returns:
        List of message dicts with "role" and "content" keys, or empty list if no history
    """
    try:
        from src.db import Group

        group = Group.get_by_id(group_id)
        if not group:
            return []

        # Fetch last N /ai command usages for this group
        command_usages = (
            CommandUsage.select()
            .where(CommandUsage.command_name == "ai")
            .where(CommandUsage.group == group)
            .where(CommandUsage.metadata.is_null(False))
            .order_by(CommandUsage.executed_at.desc())
            .limit(limit)
        )

        if not command_usages:
            # No history, return current message only
            if current_user_message:
                return [{"role": "user", "content": current_user_message}]
            return []

        # Reverse to get chronological order (oldest first)
        usages_list = list(command_usages)
        usages_list.reverse()

        # Build messages list
        messages = []
        for usage in usages_list:
            metadata = usage.metadata or {}
            user_msg = metadata.get("user_message")
            bot_resp = metadata.get("bot_response")

            if user_msg:
                messages.append({"role": "user", "content": user_msg})
            if bot_resp:
                messages.append({"role": "assistant", "content": bot_resp})

        # Add current message if provided
        if current_user_message:
            messages.append({"role": "user", "content": current_user_message})

        return messages

    except Exception as e:
        logger.warning(f"[ai] Error building conversation messages: {e}")
        # Fallback to current message only
        if current_user_message:
            return [{"role": "user", "content": current_user_message}]
        return []
