"""What /ai knows about a chat: the transcript, earlier /ai exchanges, a rolling summary
of older history, and notes it has been asked to remember."""

from dataclasses import dataclass
from datetime import datetime

from loguru import logger

from src.db import CommandUsage, Group, message_dao
from src.domain import ai

from .ai_format import (
    BOT_NAME,
    format_chat_message,
    format_header,
    format_line,
    format_time,
    truncate,
)

# How many recent chat messages go into the prompt as context
TRANSCRIPT_MESSAGE_LIMIT = 50
# How many earlier /ai exchanges can be woven into the transcript
TRANSCRIPT_AI_EXCHANGE_LIMIT = 20
# The bot's earlier replies can be long - keep enough to follow the thread
TRANSCRIPT_MAX_RESPONSE_LENGTH = 1500
# How many recent /ai exchanges to search when looking up a bot response by id
AI_RESPONSE_LOOKBACK = 500

# Older history is summarised once this many messages have scrolled out of the transcript
SUMMARY_MIN_NEW_MESSAGES = 50
# The most messages summarised in one go
SUMMARY_MAX_BATCH = 300
SUMMARY_MAX_CHARS = 3000

SUMMARY_SYSTEM_PROMPT = (
    "You maintain a running summary of a Telegram group chat, so a bot that can only see "
    "the latest messages knows what happened earlier. You get the summary so far (if any) "
    "and a batch of newer messages. Write an updated summary that folds the new messages "
    "in: the topics discussed, decisions and plans (with dates), questions left open, "
    "running jokes, and who said what when it matters. Drop details that no longer "
    "matter. Write plain prose or short bullet points, under 300 words, and nothing else."
)

# Notes /ai has been asked to remember, per group
MAX_MEMORIES = 50
MAX_MEMORY_LENGTH = 300

# Chats whose summary is being updated right now, so requests don't double up
_summaries_in_progress: set[str] = set()


@dataclass
class Transcript:
    text: str | None
    # The oldest message shown - anything older is left to the summary
    oldest_message_id: str | None = None
    # Whether the transcript is cut off, ie. there's older history it doesn't show
    truncated: bool = False


def get_thread_cleared_at(group) -> datetime | None:
    """When the AI thread was last cleared for this group, if ever."""
    metadata = getattr(group, "metadata", None) or {}
    cleared_at = metadata.get("ai_thread_cleared_at")
    if not cleared_at:
        return None
    try:
        return datetime.fromisoformat(cleared_at)
    except (TypeError, ValueError) as e:
        logger.warning(f"[ai] Error parsing clear timestamp: {e}")
        return None


def build_transcript(
    chat_id: int | str, exclude_message_ids: set[str], since: datetime | None
) -> Transcript:
    """
    Recent chat messages merged with earlier /ai exchanges, oldest first.

    The bot's own replies aren't in the message log, so they come from the
    CommandUsage rows saved for each /ai request.
    """
    try:
        messages = message_dao.get_chat_messages(
            chat_id, limit=TRANSCRIPT_MESSAGE_LIMIT, since=since
        )
        truncated = len(messages) >= TRANSCRIPT_MESSAGE_LIMIT

        # (time, order, line) - order keeps a request ahead of its response
        entries: list[tuple[datetime, int, str]] = []
        logged_ids = set()
        for m in messages:
            logged_ids.add(str(m.message_id))
            if str(m.message_id) in exclude_message_ids:
                continue
            entries.append((m.time_sent, 0, format_chat_message(m)))

        # Only weave in exchanges from the window the messages cover - unless the
        # messages go all the way back, then everything since the clear counts
        window_start = messages[0].time_sent if truncated else since

        for usage in get_ai_exchanges(chat_id, since=window_start):
            entries.extend(format_ai_exchange(usage, logged_ids | exclude_message_ids))

        entries.sort(key=lambda e: (e[0], e[1]))
        return Transcript(
            text="\n".join(line for _, _, line in entries) or None,
            oldest_message_id=str(messages[0].message_id) if messages else None,
            truncated=truncated,
        )

    except Exception as e:
        logger.warning(f"[ai] Error building transcript: {e}")
        return Transcript(text=None)


def get_ai_exchanges(chat_id: int | str, since: datetime | None) -> list[CommandUsage]:
    """Fetch the most recent /ai requests in a chat, oldest first."""
    query = (
        CommandUsage.select()
        .where(CommandUsage.command_name == "ai")
        .where(CommandUsage.group == str(chat_id))
        .where(CommandUsage.metadata.is_null(False))
    )
    if since is not None:
        query = query.where(CommandUsage.executed_at > since)

    usages = list(
        query.order_by(CommandUsage.executed_at.desc()).limit(TRANSCRIPT_AI_EXCHANGE_LIMIT)
    )
    usages.reverse()
    return usages


def response_message_ids(usage: CommandUsage) -> list[str]:
    """The ids of the messages the bot answered an /ai request with."""
    metadata = usage.metadata or {}
    ids = metadata.get("response_message_ids")
    if not isinstance(ids, list):
        single = metadata.get("response_message_id")
        ids = [single] if single is not None else []
    return [str(i) for i in ids]


def find_ai_exchange(chat_id: int | str, message_id: int | str) -> CommandUsage | None:
    """Find the /ai exchange the bot sent a message as part of, if it was one."""
    usages = (
        CommandUsage.select()
        .where(CommandUsage.command_name == "ai")
        .where(CommandUsage.group == str(chat_id))
        .where(CommandUsage.metadata.is_null(False))
        .order_by(CommandUsage.executed_at.desc())
        .limit(AI_RESPONSE_LOOKBACK)
    )
    for usage in usages:
        if str(message_id) in response_message_ids(usage):
            return usage
    return None


def is_ai_response(chat_id: int | str, message_id: int | str) -> bool:
    try:
        return find_ai_exchange(chat_id, message_id) is not None
    except Exception as e:
        logger.warning(f"[ai] Error looking up AI response: {e}")
        return False


def format_ai_exchange(
    usage: CommandUsage, skip_message_ids: set[str]
) -> list[tuple[datetime, int, str]]:
    """Transcript entries for a saved /ai request and its response."""
    metadata = usage.metadata or {}
    user_message = metadata.get("user_message")
    bot_response = metadata.get("bot_response")
    message_id = metadata.get("message_id")
    entries = []

    # Requests that are in the message log already are skipped
    if user_message and (message_id is None or str(message_id) not in skip_message_ids):
        header = format_header(message_id, usage.executed_at)
        entries.append((usage.executed_at, 1, f"{header} {user_message}"))

    if bot_response:
        response_ids = response_message_ids(usage)
        line = format_line(
            message_id=response_ids[0] if response_ids else None,
            time=usage.executed_at,
            name=BOT_NAME,
            reply_to_id=message_id,
            text=truncate(bot_response, TRANSCRIPT_MAX_RESPONSE_LENGTH),
        )
        entries.append((usage.executed_at, 2, line))

    return entries


# --- Summary of older history ----------------------------------------------


def get_summary(group, since: datetime | None) -> dict | None:
    """The group's summary of older history, unless it predates a thread clear."""
    metadata = getattr(group, "metadata", None) or {}
    summary = metadata.get("ai_summary")
    if not isinstance(summary, dict) or not summary.get("text"):
        return None
    try:
        until = datetime.fromisoformat(summary["until"])
    except (KeyError, TypeError, ValueError):
        return None
    if since is not None and until <= since:
        return None
    return {**summary, "until": until}


def format_summary(summary: dict | None) -> str | None:
    if not summary:
        return None
    return (
        f'<earlier_summary until="{format_time(summary["until"])}">\n'
        f"{summary['text']}\n"
        "</earlier_summary>"
    )


async def update_summary(
    llm_client: ai.LLMClient,
    chat_id: int | str,
    transcript: Transcript,
    since: datetime | None,
    previous: dict | None,
):
    """
    Fold the messages between the summary and the transcript into the summary.

    Runs after a response is sent, so the next request benefits. Skipped unless
    enough messages have piled up to be worth a model call.
    """
    key = str(chat_id)
    if not transcript.truncated or transcript.oldest_message_id is None:
        return
    if key in _summaries_in_progress:
        return

    _summaries_in_progress.add(key)
    try:
        start = previous["until"] if previous else since
        if since is not None and start is not None and since > start:
            start = since

        messages = message_dao.get_chat_messages(
            chat_id,
            limit=SUMMARY_MAX_BATCH,
            before_message_id=transcript.oldest_message_id,
            since=start,
        )
        if len(messages) < SUMMARY_MIN_NEW_MESSAGES:
            return

        logger.info(f"[ai] Summarising {len(messages)} older messages for chat {chat_id}")
        prompt = ""
        if previous:
            prompt += f"<summary_so_far>\n{previous['text']}\n</summary_so_far>\n\n"
        lines = "\n".join(format_chat_message(m) for m in messages)
        prompt += f"<new_messages>\n{lines}\n</new_messages>"

        text = await llm_client.complete(
            [{"role": "user", "content": prompt}],
            system_prompt=SUMMARY_SYSTEM_PROMPT,
            max_tokens=800,
        )
        text = (text or "").strip()
        if not text:
            return

        group = Group.get_by_id(key)
        metadata = group.metadata or {}
        metadata["ai_summary"] = {
            "text": truncate(text, SUMMARY_MAX_CHARS),
            "until": messages[-1].time_sent.isoformat(),
            "until_message_id": str(messages[-1].message_id),
            "updated_at": datetime.now().isoformat(),
        }
        group.metadata = metadata
        group.save()
    except Exception as e:
        logger.warning(f"[ai] Error updating summary for chat {chat_id}: {e}")
    finally:
        _summaries_in_progress.discard(key)


# --- Memory ----------------------------------------------------------------


def get_memories(group) -> list[dict]:
    metadata = getattr(group, "metadata", None) or {}
    memories = metadata.get("ai_memory")
    return [m for m in memories if isinstance(m, dict)] if isinstance(memories, list) else []


def format_memories(memories: list[dict]) -> str | None:
    if not memories:
        return None
    lines = []
    for m in memories:
        about = f" (about {m['about']})" if m.get("about") else ""
        lines.append(f"- [{m.get('id')}]{about} {m.get('text', '')}")
    return "\n".join(lines)


def _save_memories(group, memories: list[dict]):
    metadata = group.metadata or {}
    metadata["ai_memory"] = memories
    # Reassign so peewee sees the JSON field changed
    group.metadata = metadata
    group.save()


def add_memory(chat_id: int | str, text: str, about: str | None, added_by: str) -> dict:
    """Save a note to the group's memory. Raises ValueError when it can't."""
    text = (text or "").strip()
    if not text:
        raise ValueError("the note is empty")
    if len(text) > MAX_MEMORY_LENGTH:
        raise ValueError(f"notes can be at most {MAX_MEMORY_LENGTH} characters")

    # Re-read the group, so concurrent requests don't clobber each other's notes
    group = Group.get_by_id(str(chat_id))
    memories = get_memories(group)
    if len(memories) >= MAX_MEMORIES:
        raise ValueError(f"memory is full ({MAX_MEMORIES} notes) - forget something first")

    memory = {
        "id": max((m.get("id", 0) for m in memories), default=0) + 1,
        "text": text,
        "about": (about or "").strip() or None,
        "added_by": added_by,
        "added_at": datetime.now().isoformat(),
    }
    _save_memories(group, [*memories, memory])
    return memory


def remove_memory(chat_id: int | str, memory_id: int) -> dict | None:
    """Delete a note from the group's memory, returning it if it existed."""
    group = Group.get_by_id(str(chat_id))
    memories = get_memories(group)
    removed = next((m for m in memories if str(m.get("id")) == str(memory_id)), None)
    if removed is not None:
        _save_memories(group, [m for m in memories if m is not removed])
    return removed
