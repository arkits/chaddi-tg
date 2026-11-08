import asyncio
import contextlib
import os
import re
import shutil
import tempfile
import time
import traceback

from loguru import logger
from telegram import Message, ReactionTypeEmoji, Update
from telegram.constants import ChatAction, ReactionEmoji
from telegram.error import BadRequest, TelegramError
from telegram.ext import ContextTypes

from src.domain import dc, util

WEBM_RESOURCES_DIR = "resources/webm_conversions/"
UPLOAD_TIMEOUT_SECONDS = 120
# PTB's default 5s read timeout is too short - Telegram can take longer than that to
# acknowledge a video upload, which surfaces as a TimedOut even though the video was sent
UPLOAD_TIMEOUTS = {"write_timeout": UPLOAD_TIMEOUT_SECONDS, "read_timeout": UPLOAD_TIMEOUT_SECONDS}
# getFile and the file download hit the same 5s default; getFile on a large document
# can take longer than that to respond, failing the conversion before it starts
DOWNLOAD_TIMEOUTS = {"read_timeout": UPLOAD_TIMEOUT_SECONDS}

# Bot API limits: getFile refuses anything over 20MB, sendVideo anything over 50MB
MAX_DOWNLOAD_BYTES = 20 * 1024 * 1024
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
MAX_CAPTION_LENGTH = 1024

FFMPEG_TIMEOUT_SECONDS = 600
# ffmpeg is CPU heavy - cap how many run at once so a burst of webms can't starve the box
MAX_CONCURRENT_CONVERSIONS = 2
_conversion_slots = asyncio.Semaphore(MAX_CONCURRENT_CONVERSIONS)

# How often the status message is refreshed. Telegram rate limits edits in groups
# (~20/min), so don't go much lower than this
STATUS_REFRESH_SECONDS = 4
# Chat actions ("sending a video...") expire after 5s, so re-send a bit before that
CHAT_ACTION_REFRESH_SECONDS = 4

FAILED_TEXT = "(｡•́︿•̀｡) webm conversion failed (｡•́︿•̀｡)"

_DURATION_RE = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")


class ConversionError(Exception):
    """A failure with a reason worth showing to the user"""


class StatusReporter:
    """Keeps the user informed while a conversion is running.

    Status text is set by the handler as it moves through stages; a background task
    re-renders it every few seconds with a ticking elapsed timer (and ffmpeg progress
    when known), and keeps Telegram's "sending a video..." chat action alive, so the
    chat never looks frozen even when a stage takes a while.
    """

    def __init__(self, context, chat_id: int, message: Message):
        self.context = context
        self.chat_id = chat_id
        self.message = message
        self.stage = "Starting webm conversion (^◡^)"
        self.progress: float | None = None
        self.processed_seconds: float | None = None
        self.started_at = time.monotonic()
        self.stage_started_at = self.started_at
        self._last_text = message.text if isinstance(getattr(message, "text", None), str) else None
        self._task: asyncio.Task | None = None

    def set_stage(self, stage: str):
        self.stage = stage
        self.progress = None
        self.processed_seconds = None
        self.stage_started_at = time.monotonic()

    def set_progress(self, processed_seconds: float, total_seconds: float | None):
        self.processed_seconds = processed_seconds
        if total_seconds:
            self.progress = max(0.0, min(processed_seconds / total_seconds, 1.0))

    def render(self) -> str:
        lines = [self.stage]
        if self.progress is not None:
            filled = round(self.progress * 10)
            lines.append(f"[{'█' * filled}{'░' * (10 - filled)}] {self.progress:.0%}")
        elif self.processed_seconds is not None:
            lines.append(f"{util.pretty_time_delta(self.processed_seconds)} of video processed")
        elapsed = time.monotonic() - self.started_at
        lines.append(f"⏱ {util.pretty_time_delta(elapsed)}")
        return "\n".join(lines)

    async def refresh(self):
        text = self.render()
        if text == self._last_text:
            return
        try:
            await self.message.edit_text(text=text)
            self._last_text = text
        except BadRequest as e:
            # "message is not modified" is harmless, anything else is worth a log line
            if "not modified" not in str(e).lower():
                logger.warning("[webm] failed to update status message error={}", e)
        except TelegramError as e:
            logger.warning("[webm] failed to update status message error={}", e)

    async def _send_chat_action(self):
        try:
            await self.context.bot.send_chat_action(
                chat_id=self.chat_id, action=ChatAction.UPLOAD_VIDEO
            )
        except TelegramError as e:
            logger.debug("[webm] failed to send chat action error={}", e)

    async def _loop(self):
        last_status = 0.0
        while True:
            await self._send_chat_action()
            now = time.monotonic()
            if now - last_status >= STATUS_REFRESH_SECONDS:
                await self.refresh()
                last_status = now
            await asyncio.sleep(min(STATUS_REFRESH_SECONDS, CHAT_ACTION_REFRESH_SECONDS))

    def start(self):
        self._task = asyncio.create_task(self._loop())

    async def stop(self):
        if self._task is None:
            return
        self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task
        self._task = None

    async def fail(self, reason: str | None = None):
        await self.stop()
        text = FAILED_TEXT if reason is None else f"{FAILED_TEXT}\n{reason}"
        try:
            await self.message.edit_text(text=text)
        except TelegramError as e:
            logger.error("[webm] failed to edit status message with failure error={}", e)


async def react(context, message: Message, emoji: ReactionEmoji | None):
    """Best-effort reaction on the user's message - an instant "seen it" signal.

    Some chats restrict reactions, so failures are only logged.
    """
    try:
        await context.bot.set_message_reaction(
            chat_id=message.chat_id,
            message_id=message.message_id,
            reaction=[ReactionTypeEmoji(emoji)] if emoji else [],
        )
    except TelegramError as e:
        logger.debug("[webm] failed to set reaction error={}", e)


def pretty_size(num_bytes: int) -> str:
    return f"{num_bytes / (1024 * 1024):.1f} MB"


def build_ffmpeg_command(input_path: str, output_path: str) -> list[str]:
    return [
        "ffmpeg",
        "-hide_banner",
        # never wait on stdin (e.g. an "overwrite?" prompt) - it would hang forever
        "-nostdin",
        "-y",
        "-i",
        input_path,
        "-vcodec",
        "libx264",
        "-crf",
        "28",
        # yuv420p keeps the output playable on phones - webms with alpha or 4:4:4 would
        # otherwise produce an h264 profile Telegram's mobile clients can't play
        "-pix_fmt",
        "yuv420p",
        "-vf",
        "pad=ceil(iw/2)*2:ceil(ih/2)*2",
        "-movflags",
        "+faststart",
        "-progress",
        "pipe:1",
        "-nostats",
        output_path,
    ]


def parse_duration(stderr_text: str) -> float | None:
    match = _DURATION_RE.search(stderr_text)
    if match is None:
        return None
    hours, minutes, seconds = match.groups()
    total = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    return total or None


async def run_ffmpeg(input_path: str, output_path: str, status: StatusReporter) -> None:
    proc = await asyncio.create_subprocess_exec(
        *build_ffmpeg_command(input_path, output_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stderr_chunks: list[str] = []
    duration: list[float | None] = [None]

    async def read_stderr():
        # Drain stderr so ffmpeg never blocks on a full pipe; the header carries the
        # input duration, which is what lets us show a percentage
        async for raw in proc.stderr:
            line = raw.decode(errors="replace")
            stderr_chunks.append(line)
            if duration[0] is None:
                duration[0] = parse_duration(line)

    async def read_progress():
        async for raw in proc.stdout:
            key, _, value = raw.decode(errors="replace").strip().partition("=")
            # out_time_us (and, despite the name, out_time_ms) are in microseconds
            if key in ("out_time_us", "out_time_ms") and value.isdigit():
                status.set_progress(int(value) / 1_000_000, duration[0])

    try:
        await asyncio.wait_for(
            asyncio.gather(read_stderr(), read_progress(), proc.wait()),
            timeout=FFMPEG_TIMEOUT_SECONDS,
        )
    except TimeoutError:
        proc.kill()
        await proc.wait()
        raise ConversionError(
            f"ffmpeg took longer than {util.pretty_time_delta(FFMPEG_TIMEOUT_SECONDS)}"
        ) from None

    if proc.returncode != 0:
        logger.error(
            "[webm] ffmpeg exited with returncode={} stderr_tail={}",
            proc.returncode,
            "".join(stderr_chunks[-20:]),
        )
        raise ConversionError(None)


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message is None:
            return

        document = update.message.document

        # return if there is no document associated with the message
        if document is None or document.file_name is None:
            return

        # return if the document isn't a webm
        if not document.file_name.lower().endswith(".webm"):
            return

        dc.log_command_usage("webm", update)

        await convert(update.message, context)

    except Exception as e:
        logger.error(
            "Caught Error in webm.handle - {} \n {}",
            e,
            traceback.format_exc(),
        )


async def convert(source: Message, context: ContextTypes.DEFAULT_TYPE):
    document = source.document
    file_id = str(document.file_id)

    # Instant acknowledgement, before any network round trip for the status message
    await react(context, source, ReactionEmoji.EYES)

    message = await source.reply_text("Starting webm conversion (^◡^)")
    status = StatusReporter(context, source.chat_id, message)

    if document.file_size and document.file_size > MAX_DOWNLOAD_BYTES:
        await status.fail(
            f"{pretty_size(document.file_size)} is too big - "
            f"Telegram only lets bots download up to {pretty_size(MAX_DOWNLOAD_BYTES)}"
        )
        await react(context, source, ReactionEmoji.CRYING_FACE)
        return

    os.makedirs(WEBM_RESOURCES_DIR, exist_ok=True)
    # A per-conversion directory: the same webm forwarded twice has the same file_id,
    # so shared paths would let concurrent conversions clobber or delete each other's files
    work_dir = tempfile.mkdtemp(prefix="webm_", dir=WEBM_RESOURCES_DIR)
    input_path = os.path.join(work_dir, "input.webm")
    output_path = os.path.join(work_dir, "output.mp4")

    status.start()
    try:
        if _conversion_slots.locked():
            status.set_stage("Waiting for a free converter slot (・_・;)")
            await status.refresh()

        async with _conversion_slots:
            size_hint = f" ({pretty_size(document.file_size)})" if document.file_size else ""
            status.set_stage(f"Downloading webm{size_hint}...")
            await status.refresh()

            logger.info("[webm] Starting webm download - {}", file_id)
            webm_file = await context.bot.get_file(document.file_id, **DOWNLOAD_TIMEOUTS)
            await webm_file.download_to_drive(input_path, **DOWNLOAD_TIMEOUTS)
            logger.info("[webm] Finished downloading webm - {}", file_id)

            status.set_stage("Converting to mp4...")
            await status.refresh()

            logger.info("[webm] Starting webm conversion with ffmpeg - {}", file_id)
            convert_started = time.monotonic()
            await run_ffmpeg(input_path, output_path, status)
            pretty_diff = util.pretty_time_delta(time.monotonic() - convert_started)
            logger.info(
                "[webm] ffmpeg conversion complete! webm={} time_taken={}", file_id, pretty_diff
            )

        output_size = os.path.getsize(output_path)
        if output_size > MAX_UPLOAD_BYTES:
            raise ConversionError(
                f"converted video is {pretty_size(output_size)} - "
                f"Telegram only lets bots upload up to {pretty_size(MAX_UPLOAD_BYTES)}"
            )

        status.set_stage(f"Uploading mp4 ({pretty_size(output_size)})...")
        await status.refresh()

        original_sender = util.extract_pretty_name_from_tg_user(source.from_user)
        caption = build_webm_conversion_response(
            original_sender, pretty_diff, document.file_name, source.caption
        )

        logger.info("[webm] sending converted video webm={} caption={}", file_id, caption)
        with open(output_path, "rb") as f:
            await context.bot.send_video(
                chat_id=source.chat_id,
                video=f,
                caption=caption,
                supports_streaming=True,
                **UPLOAD_TIMEOUTS,
            )

        await status.stop()
        try:
            await message.delete()
        except Exception as e:
            logger.error("[webm] failed to delete message! error={}", e)
        # Clear the 👀 now that the result is in the chat
        await react(context, source, None)

    except ConversionError as e:
        logger.error("[webm] conversion failed webm={} reason={}", file_id, e)
        await status.fail(e.args[0] if e.args else None)
        await react(context, source, ReactionEmoji.CRYING_FACE)

    except Exception as e:
        logger.error(
            "Caught Error in webm.conversion - {} \n {}",
            e,
            traceback.format_exc(),
        )
        await status.fail()
        await react(context, source, ReactionEmoji.CRYING_FACE)

    finally:
        await status.stop()
        # Clean up on every path so failed conversions don't leave files behind
        shutil.rmtree(work_dir, ignore_errors=True)


def build_webm_conversion_response(original_sender, pretty_diff, file_name, caption_text):
    header = f"{original_sender} uploaded {file_name}"
    footer = f"(converted in {pretty_diff})"

    if not caption_text:
        return header + footer

    wrapper = "\n------------------------------------\n{}\n------------------------------------\n"
    # Telegram rejects captions over 1024 chars, which would fail an otherwise good
    # conversion - trim the user's caption to whatever room is left
    room = MAX_CAPTION_LENGTH - len(header) - len(footer) - len(wrapper.format(""))
    if len(caption_text) > room:
        caption_text = caption_text[: max(room - 1, 0)] + "…"

    return header + wrapper.format(caption_text) + footer
