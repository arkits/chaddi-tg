"""Downloading the photos and files /ai is asked about, and preparing them for the model."""

import mimetypes
from dataclasses import dataclass

from loguru import logger

from src.domain import ai

# Attachment limits. Bots can't download files over 20 MB from Telegram at all.
MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_PDF_BYTES = 10 * 1024 * 1024
# Anything else is read as text and pasted into the prompt
MAX_TEXT_FILE_BYTES = 1024 * 1024
MAX_TEXT_FILE_CHARS = 100_000
# Caps on what one request sends the model - an album is up to 10 photos
MAX_ATTACHMENTS = 10
MAX_TOTAL_ATTACHMENT_BYTES = 25 * 1024 * 1024

# Image formats the models accept
SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


@dataclass
class AttachedFile:
    """A file from the request or the replied-to message, and what became of it."""

    # Where the file came from - eg. "request" or "replied message"
    source: str
    # eg. 'photo' or 'file "notes.pdf"'
    label: str
    # Images and PDFs are sent to the model as attachments
    attachment: ai.LLMAttachment | None = None
    # Text files are pasted into the prompt
    text: str | None = None
    name: str | None = None
    # Why the file isn't included, when it isn't
    skipped_reason: str | None = None

    def summary(self) -> str:
        if self.skipped_reason:
            status = f"not included - {self.skipped_reason}"
        elif self.text is not None:
            status = "contents in <file> below"
        elif self.attachment is not None and self.attachment.is_image:
            status = "attached as an image"
        else:
            status = "attached"
        return f"{self.source}: {self.label} ({status})"

    def file_block(self) -> str | None:
        """The text file's contents, wrapped for the prompt."""
        if self.text is None:
            return None
        return f'<file name="{self.name}" from="{self.source}">\n{self.text}\n</file>'


class StoredFile:
    """
    A file referenced by a logged message, downloadable by its file id.

    Quacks like a PhotoSize / Document, so it goes through the same loaders.
    """

    def __init__(self, bot, data: dict):
        self.bot = bot
        self.file_id = data.get("file_id")
        self.file_size = data.get("file_size")
        self.file_name = data.get("file_name")
        self.mime_type = data.get("mime_type")

    async def get_file(self):
        return await self.bot.get_file(self.file_id)


def has_file(message) -> bool:
    return bool(message.photo) or message.document is not None


async def collect_files(message, source: str) -> list[AttachedFile]:
    """Download the photo or document on a live message, if it has one."""
    files = []
    if message.photo:
        # The largest size is last
        files.append(await load_photo(message.photo[-1], source))
    if message.document is not None:
        files.append(await load_document(message.document, source))
    return files


async def collect_stored_files(bot, message: dict, source: str) -> list[AttachedFile]:
    """Download the photo or document on a logged message, if it has one."""
    files = []
    photo = message.get("photo")
    if isinstance(photo, list) and photo and isinstance(photo[-1], dict):
        files.append(await load_photo(StoredFile(bot, photo[-1]), source))
    document = message.get("document")
    if isinstance(document, dict) and message.get("animation") is None:
        files.append(await load_document(StoredFile(bot, document), source))
    return files


def enforce_limits(files: list[AttachedFile]) -> list[AttachedFile]:
    """Drop attachments past the per-request count and size caps."""
    count = 0
    total = 0
    for f in files:
        if f.attachment is None:
            continue
        size = len(f.attachment.data)
        if count >= MAX_ATTACHMENTS or total + size > MAX_TOTAL_ATTACHMENT_BYTES:
            f.attachment = None
            f.skipped_reason = "over the per-request attachment limit"
            continue
        count += 1
        total += size
    return files


async def _download(telegram_file_holder) -> bytes:
    telegram_file = await telegram_file_holder.get_file()
    return bytes(await telegram_file.download_as_bytearray())


async def load_photo(photo, source: str) -> AttachedFile:
    file = AttachedFile(source=source, label="photo")
    size = photo.file_size if isinstance(photo.file_size, int) else None
    if size is not None and size > MAX_IMAGE_BYTES:
        file.skipped_reason = (
            f"too large ({format_size(size)}, limit {format_size(MAX_IMAGE_BYTES)})"
        )
        return file
    try:
        data = await _download(photo)
    except Exception as e:
        logger.warning(f"[ai] Failed to download photo: {e}")
        file.skipped_reason = "couldn't download it"
        return file
    logger.info(f"[ai] Downloaded photo, size={len(data)} bytes")
    file.attachment = ai.LLMAttachment(data=data, mime_type="image/jpeg")
    return file


async def load_document(document, source: str) -> AttachedFile:
    name = document.file_name if isinstance(document.file_name, str) else None
    mime_type = document.mime_type if isinstance(document.mime_type, str) else None
    mime_type = (mime_type or (name and mimetypes.guess_type(name)[0]) or "").lower()
    size = document.file_size if isinstance(document.file_size, int) else None

    file = AttachedFile(source=source, label=f'file "{name}"' if name else "file", name=name)

    if mime_type in SUPPORTED_IMAGE_TYPES:
        kind, limit = "image", MAX_IMAGE_BYTES
    elif mime_type == "application/pdf":
        kind, limit = "pdf", MAX_PDF_BYTES
    elif mime_type.startswith(("image/", "video/", "audio/")):
        file.skipped_reason = f"unsupported file type ({mime_type})"
        return file
    else:
        kind, limit = "text", MAX_TEXT_FILE_BYTES

    if size is not None and size > limit:
        file.skipped_reason = f"too large ({format_size(size)}, limit {format_size(limit)})"
        return file

    try:
        data = await _download(document)
    except Exception as e:
        logger.warning(f"[ai] Failed to download document {name}: {e}")
        file.skipped_reason = "couldn't download it"
        return file
    logger.info(f"[ai] Downloaded document {name} ({mime_type}), size={len(data)} bytes")

    if kind == "text":
        text = decode_text(data)
        if text is None:
            file.skipped_reason = f"can't read this file type ({mime_type or 'binary'})"
            return file
        file.text = truncate_text(text)
        file.name = name or "file"
    else:
        file.attachment = ai.LLMAttachment(data=data, mime_type=mime_type, filename=name)
    return file


def decode_text(data: bytes) -> str | None:
    """Decode a file as UTF-8 text, or None if it looks binary."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if "\x00" in text:
        return None
    return text


def truncate_text(text: str, limit: int = MAX_TEXT_FILE_CHARS) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n[truncated - showing the first {limit:,} of {len(text):,} characters]"


def format_size(size: int) -> str:
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    return f"{max(1, size // 1024)} KB"
