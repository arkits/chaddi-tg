import contextlib
import re
import traceback
from datetime import datetime

from loguru import logger
from peewee import DoesNotExist
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.db import CommandUsage, Group, message_dao
from src.domain import ai, dc, util

COMMAND_COST = 200

# Telegram rejects messages longer than this
MAX_MESSAGE_LENGTH = 4096

# Matches the command at the start of a photo caption, eg. "/ai" or "/ai@chaddi_bot"
COMMAND_PREFIX_RE = re.compile(r"^/ai(@\w+)?(\s+|$)", re.IGNORECASE)

CHAT_HISTORY_DEFAULT_LIMIT = 30
CHAT_HISTORY_MAX_LIMIT = 100
# Long messages are cut down in chat history tool output to keep it compact
CHAT_HISTORY_MAX_TEXT_LENGTH = 500


async def handle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    question: str | None = None,
    quiet: bool = False,
):
    """
    Handle an AI request.

    Args:
        update: The Telegram update
        context: The Telegram context
        question: The user's question. Defaults to the command args - pass this
            explicitly when invoking from a non-command message (eg. a mention).
        quiet: Skip the "not enough ₹okda" / "not enabled" / "provide a question"
            replies and bail out silently. Used by the mention path, where the
            user didn't explicitly invoke a command.
    """
    try:
        command_usage = dc.log_command_usage("ai", update)

        try:
            group = Group.get_by_id(update.effective_chat.id)
        except DoesNotExist:
            group = None
        except Exception as e:
            logger.error(f"[ai] Error checking group permissions: {e}")
            if not quiet:
                await update.message.reply_text("Something went wrong, please try again later.")
            return

        if not group or "ai" not in group.metadata.get("enabled_commands", []):
            logger.info(f"[ai] Command disabled for group {update.effective_chat.id}")
            if quiet:
                return
            await update.message.reply_text(
                "This command is not enabled for this group.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        # Check for text passed in directly, otherwise fall back to command args
        user_question = question
        if not user_question and context.args:
            user_question = " ".join(context.args)

        # Check for reply to message
        reply_message = update.message.reply_to_message
        formatted_reply_context = None
        photo = None

        if reply_message:
            # Extract text and caption from reply message
            reply_context_parts = [p for p in (reply_message.text, reply_message.caption) if p]

            # Get photo from reply (prioritize reply image over current message image)
            if reply_message.photo:
                # Get the largest photo (last in the list)
                photo = reply_message.photo[-1]

            # Format reply context with reply message author's username
            if reply_context_parts:
                reply_context = "\n".join(reply_context_parts)
                reply_username = util.extract_pretty_name_from_tg_user(reply_message.from_user)
                formatted_reply_context = f"{reply_username}: {reply_context}"

        # Check for photo in the current message (only if no image from reply)
        if photo is None and update.message.photo:
            photo = update.message.photo[-1]

        # Use caption from current message, minus the command
        # (skipped when the caller passed the question in - it already parsed the caption)
        message_text = None
        caption = update.message.caption
        if question is None and isinstance(caption, str) and caption:
            message_text = COMMAND_PREFIX_RE.sub("", caption, count=1).strip() or None

        # Use user question if there was no caption
        if not message_text and user_question:
            message_text = user_question

        if not message_text and photo is None and not formatted_reply_context:
            if quiet:
                logger.info("[ai] Nothing to respond to, skipping")
                return
            await update.message.reply_text(
                "Please provide a question, reply to a message, or send an image with `/ai`.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        # Only charge once we know the request will actually be answered
        if not util.paywall_user(update.effective_user.id, COMMAND_COST):
            if quiet:
                logger.info(f"[ai] Not enough ₹okda for user {update.effective_user.id}")
                return
            await update.message.reply_text(
                f"Sorry! You don't have enough ₹okda! Each `/ai` costs {COMMAND_COST} ₹okda.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        image_bytes = None
        image_mime_type = None
        if photo is not None:
            photo_file = await photo.get_file()
            image_bytes = bytes(await photo_file.download_as_bytearray())
            image_mime_type = "image/jpeg"
            logger.info(f"[ai] Downloaded photo, size={len(image_bytes)} bytes")

        # Default prompt for image-only requests
        if image_bytes and not message_text:
            message_text = "Describe this image."

        # Format message with username
        # If we have a reply context, combine it with the user's question/text (if any)
        if formatted_reply_context:
            if message_text:
                current_username = util.extract_pretty_name_from_tg_user(update.message.from_user)
                formatted_message = (
                    f"{formatted_reply_context}\n\n{current_username}: {message_text}"
                )
            else:
                # No user question/text, just use the formatted reply context
                formatted_message = formatted_reply_context
        else:
            # No reply, format current message with current user's username
            username = util.extract_pretty_name_from_tg_user(update.message.from_user)
            formatted_message = f"{username}: {message_text}"

        # Build conversation history for group chats
        is_group = update.message.chat.type in ("group", "supergroup")

        # Send initial "Thinking..." message
        sent_message = await update.message.reply_text("ek minute...")

        llm_client = ai.get_default_client(
            distinct_id=str(update.message.from_user.id),
            properties={"command": "ai", "chat_id": str(update.message.chat.id)},
        )

        # Build messages list with conversation history for group chats
        messages = []
        if is_group:
            messages = _build_ai_conversation_messages(
                group_id=str(update.message.chat.id),
                limit=50,
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
                preview = accumulated_text[: MAX_MESSAGE_LENGTH - 4]
                await sent_message.edit_text(preview + " ...")

        # Generate response with streaming
        response_text = await llm_client.generate_streaming(
            messages=messages,
            system_prompt=_build_system_prompt(llm_client, update.message.message_id),
            image_bytes=image_bytes,
            image_mime_type=image_mime_type,
            on_chunk=update_message,
            update_interval=1.0,
            tools=[_build_chat_history_tool(update.message.chat.id)],
        )

        # Final update
        if not response_text or not response_text.strip():
            response_text = "AI returned an empty response. Please try again."

        await _send_response(sent_message, response_text)

        # Save the conversation to CommandUsage metadata
        _save_ai_conversation(command_usage, formatted_message, response_text)

    except Exception as e:
        logger.error(f"Caught Error in ai.handle - {e} \n {traceback.format_exc()}")
        await update.message.reply_text("Something went wrong while processing your request.")


def _build_system_prompt(llm_client: ai.LLMClient, current_message_id: int) -> str:
    """Build the system prompt, only advertising capabilities the client actually has."""
    current_datetime = datetime.now().astimezone().strftime("%A, %B %d, %Y %H:%M %Z")
    system_prompt = (
        f"You are Chaddi, an AI assistant in a Telegram group. "
        f"The current date and time is {current_datetime}. "
        "You will receive messages from users and you will respond to them. "
        "Be helpful, slightly edgy, and engaging. "
        "Keep responses concise and appropriate for a group chat setting. "
        "You will receive messages from users in the format of `username: message`. "
        "Respond with just the message text in markdown format; don't prefix your response with `Chaddi:`."
    )
    if getattr(llm_client, "has_web_search", False) is True:
        system_prompt += (
            " You have access to real-time web search — use it for any question "
            "about current events, recent news, sports results, or anything time-sensitive."
        )
    if getattr(llm_client, "provider", None) in ("openai", "openrouter"):
        system_prompt += (
            " You can read the group's chat with the get_chat_history tool. Use it when "
            "you need more context - eg. what people were just talking about, what "
            "someone said earlier, or what a message is replying to. The message you "
            f"are responding to is #{current_message_id}."
        )
    return system_prompt


def _build_chat_history_tool(chat_id: int | str) -> ai.LLMTool:
    """Build a tool that lets the model read this chat's logged messages."""

    def get_chat_history(
        limit: int = CHAT_HISTORY_DEFAULT_LIMIT,
        before_message_id: int | str | None = None,
        search: str | None = None,
    ) -> str:
        limit = max(1, min(int(limit), CHAT_HISTORY_MAX_LIMIT))
        messages = message_dao.get_chat_messages(
            chat_id,
            limit=limit,
            before_message_id=before_message_id,
            search=search or None,
        )
        if not messages:
            return "No messages found."
        return "\n".join(_format_chat_message(m) for m in messages)

    return ai.LLMTool(
        name="get_chat_history",
        description=(
            "Read recent messages from this Telegram chat, oldest first. Each line looks "
            "like `[#<message_id> <time>] <user> (replying to #<id>): <text>`. Use it to "
            "catch up on the conversation, find what someone said, or follow a reply thread."
        ),
        parameters={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": (
                        f"How many messages to return, most recent first "
                        f"(default {CHAT_HISTORY_DEFAULT_LIMIT}, max {CHAT_HISTORY_MAX_LIMIT})."
                    ),
                },
                "before_message_id": {
                    "type": "integer",
                    "description": (
                        "Only return messages sent before this message id. Pass the "
                        "oldest id from a previous call to page further back."
                    ),
                },
                "search": {
                    "type": "string",
                    "description": "Only return messages containing this text (case-insensitive).",
                },
            },
            "additionalProperties": False,
        },
        handler=get_chat_history,
    )


def _format_chat_message(message) -> str:
    """Format a logged Message as a line of chat history."""
    name = util.extract_pretty_name_from_bakchod(message.from_bakchod)
    line = f"[#{message.message_id} {message.time_sent.strftime('%b %d %H:%M')}] {name}"

    reply_to_id = _get_reply_to_message_id(message.update)
    if reply_to_id is not None:
        line += f" (replying to #{reply_to_id})"

    text = message.text or ""
    if len(text) > CHAT_HISTORY_MAX_TEXT_LENGTH:
        text = text[:CHAT_HISTORY_MAX_TEXT_LENGTH] + "…"
    return f"{line}: {text}"


def _get_reply_to_message_id(update_dict) -> int | None:
    """Pull the replied-to message id out of a stored Update dict."""
    if not isinstance(update_dict, dict):
        return None
    message = update_dict.get("message")
    if not isinstance(message, dict):
        return None
    reply_to = message.get("reply_to_message")
    if not isinstance(reply_to, dict):
        return None
    return reply_to.get("message_id")


def _split_message(text: str, limit: int = MAX_MESSAGE_LENGTH) -> list[str]:
    """Split text into chunks Telegram will accept, preferring line then word breaks."""
    chunks = []
    while len(text) > limit:
        cut = text.rfind("\n", 0, limit)
        if cut <= 0:
            cut = text.rfind(" ", 0, limit)
        if cut <= 0:
            cut = limit
        chunk = text[:cut].rstrip()
        if chunk:
            chunks.append(chunk)
        text = text[cut:].lstrip()
    if text:
        chunks.append(text)
    return chunks or [""]


async def _send_with_markdown_fallback(send, text: str):
    """Send text as markdown, falling back to plain text if Telegram can't parse it."""
    try:
        return await send(text, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        return await send(text)


async def _send_response(sent_message, response_text: str):
    """Put the response in the placeholder message, spilling over into replies if too long."""
    chunks = _split_message(response_text)
    await _send_with_markdown_fallback(sent_message.edit_text, chunks[0])
    for chunk in chunks[1:]:
        await _send_with_markdown_fallback(sent_message.reply_text, chunk)


def _save_ai_conversation(command_usage: CommandUsage | None, user_message: str, bot_response: str):
    """
    Save the AI conversation to the CommandUsage logged for this request.

    Args:
        command_usage: The CommandUsage created when the command was invoked
        user_message: The user's message
        bot_response: The bot's response
    """
    if command_usage is None:
        logger.warning("[ai] No CommandUsage to save conversation to")
        return

    try:
        if command_usage.metadata is None:
            command_usage.metadata = {}
        command_usage.metadata["user_message"] = user_message
        command_usage.metadata["bot_response"] = bot_response
        command_usage.save()
        logger.debug(f"[ai] Saved conversation to CommandUsage {command_usage.id}")
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

        # Check if AI thread was cleared for this group
        clear_timestamp = None
        if group.metadata and "ai_thread_cleared_at" in group.metadata:
            try:
                clear_timestamp = datetime.fromisoformat(group.metadata["ai_thread_cleared_at"])
                logger.debug(f"[ai] Thread cleared at {clear_timestamp} for group {group_id}")
            except Exception as e:
                logger.warning(f"[ai] Error parsing clear timestamp: {e}")

        # Fetch last N /ai command usages for this group
        query = (
            CommandUsage.select()
            .where(CommandUsage.command_name == "ai")
            .where(CommandUsage.group == group)
            .where(CommandUsage.metadata.is_null(False))
        )

        # If thread was cleared, only include records after the clear timestamp
        if clear_timestamp:
            query = query.where(CommandUsage.executed_at > clear_timestamp)

        command_usages = query.order_by(CommandUsage.executed_at.desc()).limit(limit)

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
