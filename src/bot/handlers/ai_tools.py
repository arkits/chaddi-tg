"""Tools the /ai model can call - reading the chat and the web, and acting in the chat."""

import asyncio
import ipaddress
import socket
from dataclasses import dataclass
from datetime import datetime, timedelta
from html.parser import HTMLParser
from typing import ClassVar
from urllib.parse import urljoin, urlparse

import requests
from loguru import logger
from telegram import ReplyParameters

from src.db import Bakchod, message_dao
from src.domain import ai, util

from . import ai_files, ai_history, remind
from .ai_format import BOT_NAME, format_chat_message, stored_message, truncate

CHAT_HISTORY_DEFAULT_LIMIT = 30
CHAT_HISTORY_MAX_LIMIT = 100

# Web pages are fetched with these limits
FETCH_TIMEOUT_SECONDS = 10
FETCH_MAX_BYTES = 2 * 1024 * 1024
FETCH_MAX_REDIRECTS = 5
FETCH_MAX_CHARS = 20_000
FETCH_USER_AGENT = "Mozilla/5.0 (compatible; ChaddiBot/1.0; +https://github.com/arkits/chaddi-tg)"

# Actions are capped per request, and some cost ₹okda on top of the /ai fee
MAX_IMAGES_PER_REQUEST = 1
MAX_POLLS_PER_REQUEST = 1
MAX_REMINDERS_PER_REQUEST = 3
MAX_MEMORY_CHANGES_PER_REQUEST = 5
IMAGE_COST = 500

MIN_REMINDER_SECONDS = 60
MAX_REMINDER_SECONDS = 365 * 24 * 60 * 60


@dataclass
class ToolContext:
    """What the tools need to know about the request they're serving."""

    bot: object
    job_queue: object
    chat_id: int
    # The /ai message - actions reply to it
    request_message_id: int
    user_id: int
    user_name: str
    images_generated: int = 0
    polls_created: int = 0
    reminders_set: int = 0
    memory_changes: int = 0


def build_tools(ctx: ToolContext) -> list[ai.LLMTool]:
    return [
        chat_history_tool(ctx.chat_id),
        read_message_tool(ctx),
        fetch_url_tool(),
        set_reminder_tool(ctx),
        generate_image_tool(ctx),
        create_poll_tool(ctx),
        remember_tool(ctx),
        forget_tool(ctx),
    ]


# --- Reading the chat --------------------------------------------------------


def chat_history_tool(chat_id: int | str) -> ai.LLMTool:
    """A tool that lets the model read this chat's logged messages."""

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
        return "\n".join(format_chat_message(m) for m in messages)

    def status(args: dict) -> str:
        if args.get("search"):
            return f'🔎 searching the chat for "{truncate(str(args["search"]), 40)}"…'
        return "📜 scrolling up the chat…"

    return ai.LLMTool(
        name="get_chat_history",
        description=(
            "Read messages from this Telegram chat, oldest first. Each line looks like "
            "`[#<message_id> <time>] <user> (replying to #<id>): <text>`. Use it to read "
            "further back than the transcript, find what someone said, or follow a reply thread."
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
        status=status,
    )


def read_message_tool(ctx: ToolContext) -> ai.LLMTool:
    """A tool that opens one message - its full text, and any photo or file on it."""

    async def read_message(message_id: int | str) -> ai.ToolResult:
        logged = message_dao.get_message(ctx.chat_id, message_id)
        if logged is not None:
            files = await ai_files.collect_stored_files(
                ctx.bot, stored_message(logged), f"message #{message_id}"
            )
            files = ai_files.enforce_limits(files)
            parts = [format_chat_message(logged, max_text_length=4000)]
            parts += [f"- {f.summary()}" for f in files]
            parts += [block for f in files if (block := f.file_block())]
            return ai.ToolResult(
                text="\n".join(parts),
                attachments=[f.attachment for f in files if f.attachment is not None],
            )

        usage = ai_history.find_ai_exchange(ctx.chat_id, message_id)
        if usage is not None:
            response = (usage.metadata or {}).get("bot_response", "")
            return ai.ToolResult(f"[#{message_id}] {BOT_NAME}: {response}")

        return ai.ToolResult(
            f"Message #{message_id} not found - it may be older than the bot's logs, or "
            "one the bot couldn't see."
        )

    return ai.LLMTool(
        name="read_message",
        description=(
            "Open a message from this chat by its id: its full text, plus any photo, PDF or "
            "text file attached to it. Use it to look at media that only shows up as "
            "[photo] or [file: …] in the transcript."
        ),
        parameters={
            "type": "object",
            "properties": {
                "message_id": {"type": "integer", "description": "The message's id (#<id>)."}
            },
            "required": ["message_id"],
            "additionalProperties": False,
        },
        handler=read_message,
        status=lambda args: f"👀 looking at message #{args.get('message_id')}…",
    )


# --- Reading the web ---------------------------------------------------------


class _TextExtractor(HTMLParser):
    """Pulls the readable text and title out of an HTML page."""

    SKIP: ClassVar[set[str]] = {"script", "style", "noscript", "svg", "template", "head"}
    BLOCK: ClassVar[set[str]] = {
        "p",
        "div",
        "br",
        "li",
        "tr",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "section",
        "article",
    }

    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self.title = ""
        self._skip_depth = 0
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self._in_title = True
        elif tag in self.SKIP:
            self._skip_depth += 1
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag in self.SKIP and self._skip_depth:
            self._skip_depth -= 1
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif not self._skip_depth:
            self.parts.append(data)

    def text(self) -> str:
        lines = (" ".join(line.split()) for line in "".join(self.parts).splitlines())
        return "\n".join(line for line in lines if line)


def html_to_text(html: str) -> tuple[str, str]:
    """Return (title, readable text) for an HTML page."""
    parser = _TextExtractor()
    parser.feed(html)
    parser.close()
    return " ".join(parser.title.split()), parser.text()


def check_public_url(url: str):
    """Refuse URLs that aren't http(s) or that point at private addresses."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("only http and https URLs can be fetched")
    if not parsed.hostname:
        raise ValueError("the URL has no host")

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(parsed.hostname, port)}
    except socket.gaierror as e:
        raise ValueError(f"couldn't resolve {parsed.hostname}") from e
    for address in addresses:
        if not ipaddress.ip_address(address.split("%")[0]).is_global:
            raise ValueError(f"{parsed.hostname} points to a private address")


def fetch_url(url: str) -> tuple[str, str, bytes, bool]:
    """
    Fetch a public URL, following redirects that stay public.

    Returns (final url, content type, body, whether the body was cut off).
    """
    for _ in range(FETCH_MAX_REDIRECTS + 1):
        check_public_url(url)
        response = requests.get(
            url,
            stream=True,
            timeout=FETCH_TIMEOUT_SECONDS,
            allow_redirects=False,
            headers={"User-Agent": FETCH_USER_AGENT},
        )
        try:
            if response.is_redirect and "location" in response.headers:
                url = urljoin(url, response.headers["location"])
                continue
            if response.status_code >= 400:
                raise ValueError(f"the server returned HTTP {response.status_code}")

            body = b""
            truncated = False
            for chunk in response.iter_content(64 * 1024):
                body += chunk
                if len(body) > FETCH_MAX_BYTES:
                    body = body[:FETCH_MAX_BYTES]
                    truncated = True
                    break
            content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
            return url, content_type, body, truncated
        finally:
            response.close()
    raise ValueError("too many redirects")


def fetch_url_tool() -> ai.LLMTool:
    """A tool that reads a web page, image or PDF from a link."""

    async def fetch(url: str) -> ai.ToolResult:
        final_url, content_type, body, truncated = await asyncio.to_thread(fetch_url, url)

        if content_type in ai_files.SUPPORTED_IMAGE_TYPES or content_type == "application/pdf":
            if truncated:
                return ai.ToolResult(f"{final_url} is too large to read.")
            attachment = ai.LLMAttachment(
                data=body,
                mime_type=content_type,
                filename=urlparse(final_url).path.rsplit("/", 1)[-1] or None,
            )
            kind = "image" if attachment.is_image else "PDF"
            return ai.ToolResult(f"Fetched {final_url} - the {kind} is attached.", [attachment])

        text = body.decode("utf-8", errors="replace")
        title = ""
        if content_type in ("text/html", "application/xhtml+xml") or "<html" in text[:1000].lower():
            title, text = html_to_text(text)
        elif not (content_type.startswith("text/") or content_type.endswith(("json", "xml"))):
            return ai.ToolResult(
                f"Can't read {final_url} - unsupported content type {content_type}."
            )

        header = f"URL: {final_url}" + (f"\nTitle: {title}" if title else "")
        if truncated or len(text) > FETCH_MAX_CHARS:
            text = text[:FETCH_MAX_CHARS] + "\n[page cut off]"
        return ai.ToolResult(f"{header}\n\n{text or '(no readable text)'}")

    def status(args: dict) -> str:
        host = urlparse(str(args.get("url", ""))).hostname or "a link"
        return f"🌐 opening {host}…"

    return ai.LLMTool(
        name="fetch_url",
        description=(
            "Fetch a web page, image or PDF from a URL and read it. Use it when someone "
            "shares a link or asks about one. Pages are returned as plain text."
        ),
        parameters={
            "type": "object",
            "properties": {"url": {"type": "string", "description": "The http(s) URL."}},
            "required": ["url"],
            "additionalProperties": False,
        },
        handler=fetch,
        status=status,
    )


# --- Acting in the chat ------------------------------------------------------


def _reply_to(ctx: ToolContext) -> ReplyParameters:
    return ReplyParameters(message_id=ctx.request_message_id, allow_sending_without_reply=True)


def set_reminder_tool(ctx: ToolContext) -> ai.LLMTool:
    def set_reminder(
        message: str, delay_minutes: float | None = None, remind_at: str | None = None
    ) -> str:
        if ctx.reminders_set >= MAX_REMINDERS_PER_REQUEST:
            return f"Error: at most {MAX_REMINDERS_PER_REQUEST} reminders per request."
        if remind.has_too_many_reminders(ctx.user_id):
            return "Error: this user has too many pending reminders already."

        now = datetime.now()
        if remind_at:
            due_at = datetime.fromisoformat(remind_at)
            if due_at.tzinfo is not None:
                due_at = due_at.astimezone().replace(tzinfo=None)
        elif delay_minutes is not None:
            due_at = now + timedelta(minutes=float(delay_minutes))
        else:
            return "Error: pass delay_minutes or remind_at."

        due_seconds = int((due_at - now).total_seconds())
        if not MIN_REMINDER_SECONDS <= due_seconds <= MAX_REMINDER_SECONDS:
            return "Error: reminders must be between a minute and a year from now."

        sj = remind.schedule_reminder(
            ctx.job_queue,
            chat_id=ctx.chat_id,
            from_bakchod_id=ctx.user_id,
            reply_to_message_id=ctx.request_message_id,
            due_seconds=due_seconds,
            reminder_message=(message or "").strip()[:500],
        )
        ctx.reminders_set += 1
        return (
            f"Reminder #{sj.job_id} set for {due_at.strftime('%a %b %d %H:%M')} "
            f"({util.pretty_time_delta(due_seconds)} from now). The bot will reply to the "
            "request message with it then."
        )

    return ai.LLMTool(
        name="set_reminder",
        description=(
            "Schedule a reminder in this chat for the person who made the request. The bot "
            "replies to their message with the reminder text when it's due. Only use it "
            "when someone asks to be reminded."
        ),
        parameters={
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "What to remind them about."},
                "delay_minutes": {
                    "type": "number",
                    "description": "Minutes from now. Pass this or remind_at.",
                },
                "remind_at": {
                    "type": "string",
                    "description": (
                        "When to remind, as an ISO 8601 local date-time "
                        "(eg. 2026-10-16T20:00). Pass this or delay_minutes."
                    ),
                },
            },
            "required": ["message"],
            "additionalProperties": False,
        },
        handler=set_reminder,
        status=lambda args: "⏰ setting a reminder…",
    )


def _refund(user_id, amount: int):
    try:
        bakchod = Bakchod.get_by_id(user_id)
        bakchod.rokda = bakchod.rokda + amount
        bakchod.save()
    except Exception as e:
        logger.warning(f"[ai] Failed to refund {amount} ₹okda to {user_id}: {e}")


def generate_image_tool(ctx: ToolContext) -> ai.LLMTool:
    async def generate_image(prompt: str) -> str:
        if ctx.images_generated >= MAX_IMAGES_PER_REQUEST:
            return f"Error: at most {MAX_IMAGES_PER_REQUEST} image per request."
        prompt = (prompt or "").strip()
        if not prompt:
            return "Error: the prompt is empty."
        if not util.paywall_user(ctx.user_id, IMAGE_COST):
            return f"Error: {ctx.user_name} doesn't have the {IMAGE_COST} ₹okda an image costs."

        try:
            image = await ai.generate_image(prompt)
            sent = await ctx.bot.send_photo(
                chat_id=ctx.chat_id,
                photo=image.data,
                caption=truncate(prompt, 1000),
                reply_parameters=_reply_to(ctx),
            )
        except Exception:
            _refund(ctx.user_id, IMAGE_COST)
            raise

        ctx.images_generated += 1
        return (
            f"The image was posted to the chat as message #{sent.message_id} "
            f"({IMAGE_COST} ₹okda charged). Don't describe it in detail - they can see it."
        )

    return ai.LLMTool(
        name="generate_image",
        description=(
            f"Generate an image from a text prompt and post it to the chat. Costs the "
            f"requester {IMAGE_COST} ₹okda, so only use it when someone asks for a picture."
        ),
        parameters={
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "A detailed description of the image to generate.",
                }
            },
            "required": ["prompt"],
            "additionalProperties": False,
        },
        handler=generate_image,
        status=lambda args: "🎨 drawing…",
    )


def create_poll_tool(ctx: ToolContext) -> ai.LLMTool:
    async def create_poll(
        question: str,
        options: list[str],
        allows_multiple_answers: bool = False,
        anonymous: bool = False,
    ) -> str:
        if ctx.polls_created >= MAX_POLLS_PER_REQUEST:
            return f"Error: at most {MAX_POLLS_PER_REQUEST} poll per request."
        options = [str(o).strip()[:100] for o in options or [] if str(o).strip()]
        if not 2 <= len(options) <= 10:
            return "Error: polls need between 2 and 10 options."
        question = (question or "").strip()[:300]
        if not question:
            return "Error: the question is empty."

        sent = await ctx.bot.send_poll(
            chat_id=ctx.chat_id,
            question=question,
            options=options,
            is_anonymous=bool(anonymous),
            allows_multiple_answers=bool(allows_multiple_answers),
            reply_parameters=_reply_to(ctx),
        )
        ctx.polls_created += 1
        return f"The poll was posted to the chat as message #{sent.message_id}."

    return ai.LLMTool(
        name="create_poll",
        description=(
            "Post a Telegram poll in the chat. Only use it when someone asks for a poll or a vote."
        ),
        parameters={
            "type": "object",
            "properties": {
                "question": {"type": "string"},
                "options": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "2 to 10 answer options.",
                },
                "allows_multiple_answers": {"type": "boolean"},
                "anonymous": {"type": "boolean", "description": "Defaults to false."},
            },
            "required": ["question", "options"],
            "additionalProperties": False,
        },
        handler=create_poll,
        status=lambda args: "📊 making a poll…",
    )


# --- Memory ------------------------------------------------------------------


def _check_memory_budget(ctx: ToolContext) -> str | None:
    if ctx.memory_changes >= MAX_MEMORY_CHANGES_PER_REQUEST:
        return f"Error: at most {MAX_MEMORY_CHANGES_PER_REQUEST} memory changes per request."
    return None


def remember_tool(ctx: ToolContext) -> ai.LLMTool:
    def remember(note: str, about: str | None = None) -> str:
        if error := _check_memory_budget(ctx):
            return error
        try:
            memory = ai_history.add_memory(ctx.chat_id, note, about, added_by=ctx.user_name)
        except ValueError as e:
            return f"Error: {e}"
        ctx.memory_changes += 1
        return f"Saved as note [{memory['id']}]."

    return ai.LLMTool(
        name="remember",
        description=(
            "Save a note to this group's long-term memory. Notes are shown to you on every "
            "request, even after the thread is cleared. Use it when someone asks you to "
            "remember something, or tells you something clearly worth knowing next time "
            "(preferences, birthdays, plans, running jokes). Don't save passwords, private "
            "details or things that only matter right now."
        ),
        parameters={
            "type": "object",
            "properties": {
                "note": {"type": "string", "description": "The fact, in one short sentence."},
                "about": {
                    "type": "string",
                    "description": "Who it's about, eg. @minji - leave out for the whole group.",
                },
            },
            "required": ["note"],
            "additionalProperties": False,
        },
        handler=remember,
        status=lambda args: "🧠 noting that down…",
    )


def forget_tool(ctx: ToolContext) -> ai.LLMTool:
    def forget(note_id: int) -> str:
        if error := _check_memory_budget(ctx):
            return error
        removed = ai_history.remove_memory(ctx.chat_id, note_id)
        if removed is None:
            return f"There's no note [{note_id}]."
        ctx.memory_changes += 1
        return f"Forgot note [{note_id}]: {removed.get('text')}"

    return ai.LLMTool(
        name="forget",
        description=(
            "Delete a note from this group's memory by its id. Use it when someone asks you "
            "to forget something, or a note is wrong or out of date."
        ),
        parameters={
            "type": "object",
            "properties": {"note_id": {"type": "integer"}},
            "required": ["note_id"],
            "additionalProperties": False,
        },
        handler=forget,
        status=lambda args: "🧹 forgetting…",
    )
