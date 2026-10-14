from unittest.mock import MagicMock

from src.bot.handlers import ai_files
from src.domain.ai import LLMAttachment


def _attached(size, source="request"):
    return ai_files.AttachedFile(
        source=source, label="photo", attachment=LLMAttachment(b"x" * size, "image/jpeg")
    )


def test_enforce_limits_caps_count():
    files = [_attached(1) for _ in range(ai_files.MAX_ATTACHMENTS + 2)]

    ai_files.enforce_limits(files)

    kept = [f for f in files if f.attachment is not None]
    assert len(kept) == ai_files.MAX_ATTACHMENTS
    assert files[-1].skipped_reason == "over the per-request attachment limit"


def test_enforce_limits_caps_total_size():
    half = ai_files.MAX_TOTAL_ATTACHMENT_BYTES // 2
    files = [_attached(half), _attached(half), _attached(half)]

    ai_files.enforce_limits(files)

    assert [f.attachment is not None for f in files] == [True, True, False]


def test_stored_file_downloads_by_id():
    bot = MagicMock()
    stored = ai_files.StoredFile(bot, {"file_id": "abc", "file_size": 5, "file_name": "a.txt"})

    assert (stored.file_id, stored.file_size, stored.file_name, stored.mime_type) == (
        "abc",
        5,
        "a.txt",
        None,
    )


def test_format_size():
    assert ai_files.format_size(10) == "1 KB"
    assert ai_files.format_size(5 * 1024) == "5 KB"
    assert ai_files.format_size(3 * 1024 * 1024) == "3.0 MB"
