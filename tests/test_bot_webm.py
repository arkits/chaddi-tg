import asyncio
import os
import shutil
import subprocess
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Document, Message, ReactionTypeEmoji, Update, User
from telegram.constants import ChatAction, ReactionEmoji
from telegram.error import BadRequest, TimedOut
from telegram.ext import ContextTypes

from src.bot.handlers import webm

FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None


@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.from_user = MagicMock(spec=User)
    return update


@pytest.fixture
def mock_context():
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = MagicMock()
    context.bot.set_message_reaction = AsyncMock()
    context.bot.send_chat_action = AsyncMock()
    context.bot.send_video = AsyncMock()
    return context


@pytest.fixture
def work_root(tmp_path, monkeypatch):
    root = str(tmp_path / "webm_conversions") + "/"
    monkeypatch.setattr(webm, "WEBM_RESOURCES_DIR", root)
    return root


@pytest.fixture
def webm_update(mock_update, mock_context):
    """An update carrying a webm document, with the status message and download mocked"""
    document = MagicMock(spec=Document)
    document.file_name = "video.webm"
    document.file_id = "testfile123"
    document.file_size = 1024 * 1024
    mock_update.message.document = document
    mock_update.message.chat_id = 999
    mock_update.message.message_id = 42
    mock_update.message.from_user.id = 111
    mock_update.message.from_user.username = "testuser"
    mock_update.message.from_user.first_name = "Test"
    mock_update.message.caption = "Test caption"

    status_message = MagicMock()
    status_message.text = "Starting webm conversion (^◡^)"
    status_message.edit_text = AsyncMock()
    status_message.delete = AsyncMock()
    mock_update.message.reply_text = AsyncMock(return_value=status_message)

    webm_file = MagicMock()

    async def download(path, **kwargs):
        with open(path, "wb") as f:
            f.write(b"webm")

    webm_file.download_to_drive = AsyncMock(side_effect=download)
    mock_context.bot.get_file = AsyncMock(return_value=webm_file)
    return mock_update, status_message, webm_file


async def fake_ffmpeg_success(input_path, output_path, status):
    with open(output_path, "wb") as f:
        f.write(b"mp4")


def reactions_set(mock_context):
    return [c.kwargs["reaction"] for c in mock_context.bot.set_message_reaction.call_args_list]


# --- early returns ---------------------------------------------------------------------


@pytest.mark.asyncio
async def test_handle_no_document(mock_update, mock_context):
    mock_update.message.document = None

    await webm.handle(mock_update, mock_context)

    assert not mock_update.message.reply_text.called


@pytest.mark.asyncio
async def test_handle_no_file_name(mock_update, mock_context):
    mock_document = MagicMock(spec=Document)
    mock_document.file_name = None
    mock_update.message.document = mock_document

    await webm.handle(mock_update, mock_context)

    assert not mock_update.message.reply_text.called


@pytest.mark.asyncio
async def test_handle_not_webm_file(mock_update, mock_context):
    mock_document = MagicMock(spec=Document)
    mock_document.file_name = "video.mp4"
    mock_update.message.document = mock_document

    await webm.handle(mock_update, mock_context)

    assert not mock_update.message.reply_text.called


@pytest.mark.asyncio
async def test_handle_no_message(mock_update, mock_context):
    mock_update.message = None

    await webm.handle(mock_update, mock_context)

    assert mock_update.message is None


@pytest.mark.asyncio
async def test_handle_uppercase_extension_is_converted(webm_update, mock_context, work_root):
    update, _, _ = webm_update
    update.message.document.file_name = "VIDEO.WEBM"

    with (
        patch("src.bot.handlers.webm.dc"),
        patch("src.bot.handlers.webm.run_ffmpeg", side_effect=fake_ffmpeg_success),
    ):
        await webm.handle(update, mock_context)

    mock_context.bot.send_video.assert_called_once()


@pytest.mark.asyncio
async def test_handle_swallows_reply_failure(webm_update, mock_context, work_root):
    update, _, _ = webm_update
    update.message.reply_text = AsyncMock(side_effect=TimedOut())

    with patch("src.bot.handlers.webm.dc"):
        await webm.handle(update, mock_context)

    mock_context.bot.get_file.assert_not_called()


# --- caption ---------------------------------------------------------------------------


def test_build_webm_conversion_response_basic():
    result = webm.build_webm_conversion_response("John", "1 minute", "video.webm", None)

    assert result == "John uploaded video.webm(converted in 1 minute)"


def test_build_webm_conversion_response_with_caption():
    caption = "This is a caption"
    result = webm.build_webm_conversion_response("Alice", "2 minutes", "test.webm", caption)

    assert "Alice uploaded test.webm" in result
    assert "2 minutes" in result
    assert caption in result
    assert "------------------------------------" in result


def test_build_webm_conversion_response_empty_caption():
    result = webm.build_webm_conversion_response("Bob", "30 seconds", "file.webm", "")

    assert "Bob" in result
    assert "file.webm" in result
    assert "30 seconds" in result
    assert "------" not in result


def test_build_webm_conversion_response_truncates_long_caption():
    result = webm.build_webm_conversion_response("Bob", "3s", "file.webm", "x" * 2000)

    assert len(result) <= webm.MAX_CAPTION_LENGTH
    assert result.endswith("(converted in 3s)")
    assert "…" in result


# --- full conversion flow --------------------------------------------------------------


@pytest.mark.asyncio
async def test_handle_webm_file_success(webm_update, mock_context, work_root):
    update, status_message, webm_file = webm_update

    with (
        patch("src.bot.handlers.webm.dc") as mock_dc,
        patch("src.bot.handlers.webm.run_ffmpeg", side_effect=fake_ffmpeg_success),
    ):
        await webm.handle(update, mock_context)

    mock_dc.log_command_usage.assert_called_once_with("webm", update)
    update.message.reply_text.assert_called_once_with("Starting webm conversion (^◡^)")
    status_message.delete.assert_called_once()

    # status message walked through the stages
    stages = [c.kwargs["text"].splitlines()[0] for c in status_message.edit_text.call_args_list]
    assert any(s.startswith("Downloading webm (1.0 MB)") for s in stages)
    assert "Converting to mp4..." in stages
    assert any(s.startswith("Uploading mp4") for s in stages)
    assert not any(webm.FAILED_TEXT in s for s in stages)

    assert mock_context.bot.get_file.call_args.kwargs["read_timeout"] == (
        webm.UPLOAD_TIMEOUT_SECONDS
    )
    assert webm_file.download_to_drive.call_args.kwargs["read_timeout"] == (
        webm.UPLOAD_TIMEOUT_SECONDS
    )

    send_kwargs = mock_context.bot.send_video.call_args.kwargs
    assert send_kwargs["chat_id"] == 999
    assert send_kwargs["read_timeout"] == webm.UPLOAD_TIMEOUT_SECONDS
    assert send_kwargs["write_timeout"] == webm.UPLOAD_TIMEOUT_SECONDS
    assert send_kwargs["supports_streaming"] is True
    assert "Test caption" in send_kwargs["caption"]

    # 👀 on arrival, cleared once the video is posted
    assert reactions_set(mock_context) == [[ReactionTypeEmoji(ReactionEmoji.EYES)], []]

    # per-conversion work dir is gone
    assert os.listdir(work_root) == []


@pytest.mark.asyncio
async def test_handle_webm_file_ffmpeg_failure(webm_update, mock_context, work_root):
    update, status_message, _ = webm_update

    with (
        patch("src.bot.handlers.webm.dc"),
        patch(
            "src.bot.handlers.webm.run_ffmpeg",
            side_effect=webm.ConversionError(None),
        ),
    ):
        await webm.handle(update, mock_context)

    status_message.edit_text.assert_called_with(text=webm.FAILED_TEXT)
    mock_context.bot.send_video.assert_not_called()
    assert reactions_set(mock_context)[-1] == [ReactionTypeEmoji(ReactionEmoji.CRYING_FACE)]
    assert os.listdir(work_root) == []


@pytest.mark.asyncio
async def test_handle_webm_file_download_error(webm_update, mock_context, work_root):
    update, status_message, _ = webm_update
    mock_context.bot.get_file = AsyncMock(side_effect=Exception("Download error"))

    with patch("src.bot.handlers.webm.dc"):
        await webm.handle(update, mock_context)

    status_message.edit_text.assert_called_with(text=webm.FAILED_TEXT)
    assert os.listdir(work_root) == []


@pytest.mark.asyncio
async def test_handle_webm_file_upload_timeout_cleans_up(webm_update, mock_context, work_root):
    update, status_message, _ = webm_update
    mock_context.bot.send_video = AsyncMock(side_effect=TimedOut())

    with (
        patch("src.bot.handlers.webm.dc"),
        patch("src.bot.handlers.webm.run_ffmpeg", side_effect=fake_ffmpeg_success),
    ):
        await webm.handle(update, mock_context)

    status_message.edit_text.assert_called_with(text=webm.FAILED_TEXT)
    status_message.delete.assert_not_called()
    assert os.listdir(work_root) == []


@pytest.mark.asyncio
async def test_handle_rejects_file_over_download_limit(webm_update, mock_context, work_root):
    update, status_message, _ = webm_update
    update.message.document.file_size = webm.MAX_DOWNLOAD_BYTES + 1

    with patch("src.bot.handlers.webm.dc"):
        await webm.handle(update, mock_context)

    mock_context.bot.get_file.assert_not_called()
    text = status_message.edit_text.call_args.kwargs["text"]
    assert text.startswith(webm.FAILED_TEXT)
    assert "too big" in text


@pytest.mark.asyncio
async def test_handle_rejects_output_over_upload_limit(
    webm_update, mock_context, work_root, monkeypatch
):
    update, status_message, _ = webm_update
    monkeypatch.setattr(webm, "MAX_UPLOAD_BYTES", 1)

    with (
        patch("src.bot.handlers.webm.dc"),
        patch("src.bot.handlers.webm.run_ffmpeg", side_effect=fake_ffmpeg_success),
    ):
        await webm.handle(update, mock_context)

    mock_context.bot.send_video.assert_not_called()
    text = status_message.edit_text.call_args.kwargs["text"]
    assert "upload up to" in text
    assert os.listdir(work_root) == []


@pytest.mark.asyncio
async def test_handle_survives_reaction_and_delete_failures(webm_update, mock_context, work_root):
    update, status_message, _ = webm_update
    mock_context.bot.set_message_reaction = AsyncMock(side_effect=BadRequest("Reactions off"))
    status_message.delete = AsyncMock(side_effect=Exception("can't delete"))

    with (
        patch("src.bot.handlers.webm.dc"),
        patch("src.bot.handlers.webm.run_ffmpeg", side_effect=fake_ffmpeg_success),
    ):
        await webm.handle(update, mock_context)

    mock_context.bot.send_video.assert_called_once()


@pytest.mark.asyncio
async def test_concurrent_conversions_of_same_file_dont_collide(
    webm_update, mock_context, work_root
):
    """The same webm forwarded twice shares a file_id - each run needs its own files"""
    update, _, _ = webm_update
    seen_inputs = []

    async def slow_ffmpeg(input_path, output_path, status):
        seen_inputs.append(input_path)
        await asyncio.sleep(0.05)
        assert os.path.exists(input_path)
        await fake_ffmpeg_success(input_path, output_path, status)

    with (
        patch("src.bot.handlers.webm.dc"),
        patch("src.bot.handlers.webm.run_ffmpeg", side_effect=slow_ffmpeg),
    ):
        await asyncio.gather(webm.handle(update, mock_context), webm.handle(update, mock_context))

    assert len(set(seen_inputs)) == 2
    assert mock_context.bot.send_video.call_count == 2


# --- status reporter -------------------------------------------------------------------


def make_reporter(mock_context):
    message = MagicMock()
    message.text = "Starting webm conversion (^◡^)"
    message.edit_text = AsyncMock()
    return webm.StatusReporter(mock_context, 123, message), message


def test_status_render_with_progress(mock_context):
    reporter, _ = make_reporter(mock_context)
    reporter.set_stage("Converting to mp4...")
    reporter.set_progress(5, 10)

    lines = reporter.render().splitlines()

    assert lines[0] == "Converting to mp4..."
    assert lines[1] == "[█████░░░░░] 50%"
    assert lines[2].startswith("⏱ ")


def test_status_render_without_duration(mock_context):
    reporter, _ = make_reporter(mock_context)
    reporter.set_stage("Converting to mp4...")
    reporter.set_progress(65, None)

    assert "1m 5s of video processed" in reporter.render()


def test_status_set_stage_resets_progress(mock_context):
    reporter, _ = make_reporter(mock_context)
    reporter.set_progress(5, 10)
    reporter.set_stage("Uploading")

    assert reporter.progress is None
    assert len(reporter.render().splitlines()) == 2


@pytest.mark.asyncio
async def test_status_refresh_skips_unchanged_text(mock_context):
    reporter, message = make_reporter(mock_context)
    reporter.set_stage("Downloading")

    await reporter.refresh()
    await reporter.refresh()

    message.edit_text.assert_called_once()


@pytest.mark.asyncio
async def test_status_refresh_swallows_telegram_errors(mock_context):
    reporter, message = make_reporter(mock_context)
    message.edit_text = AsyncMock(side_effect=BadRequest("Message is not modified"))
    reporter.set_stage("Downloading")
    await reporter.refresh()

    message.edit_text = AsyncMock(side_effect=TimedOut())
    reporter.set_stage("Converting")
    await reporter.refresh()


@pytest.mark.asyncio
async def test_status_heartbeat_sends_chat_action_and_ticks(mock_context, monkeypatch):
    monkeypatch.setattr(webm, "STATUS_REFRESH_SECONDS", 0.01)
    monkeypatch.setattr(webm, "CHAT_ACTION_REFRESH_SECONDS", 0.01)
    reporter, message = make_reporter(mock_context)
    reporter.set_stage("Converting to mp4...")

    reporter.start()
    await asyncio.sleep(0.05)
    await reporter.stop()
    await reporter.stop()  # idempotent

    mock_context.bot.send_chat_action.assert_called_with(
        chat_id=123, action=ChatAction.UPLOAD_VIDEO
    )
    message.edit_text.assert_called()


@pytest.mark.asyncio
async def test_status_heartbeat_survives_chat_action_failure(mock_context, monkeypatch):
    monkeypatch.setattr(webm, "STATUS_REFRESH_SECONDS", 0.01)
    monkeypatch.setattr(webm, "CHAT_ACTION_REFRESH_SECONDS", 0.01)
    mock_context.bot.send_chat_action = AsyncMock(side_effect=TimedOut())
    reporter, _ = make_reporter(mock_context)

    reporter.start()
    await asyncio.sleep(0.03)

    assert not reporter._task.done()
    await reporter.stop()


@pytest.mark.asyncio
async def test_status_fail_swallows_edit_error(mock_context):
    reporter, message = make_reporter(mock_context)
    message.edit_text = AsyncMock(side_effect=TimedOut())

    await reporter.fail("nope")

    message.edit_text.assert_called_once_with(text=f"{webm.FAILED_TEXT}\nnope")


# --- ffmpeg ----------------------------------------------------------------------------


def test_parse_duration():
    assert webm.parse_duration("  Duration: 00:01:02.50, start: 0.000000") == 62.5
    assert webm.parse_duration("  Duration: N/A, start: 0.000000") is None
    assert webm.parse_duration("Stream #0:0: Video: vp9") is None


def test_build_ffmpeg_command_is_non_interactive():
    cmd = webm.build_ffmpeg_command("in.webm", "out.mp4")

    assert cmd[0] == "ffmpeg"
    assert "-nostdin" in cmd
    assert "-y" in cmd
    assert cmd[-1] == "out.mp4"
    assert cmd[cmd.index("-i") + 1] == "in.webm"


@pytest.mark.asyncio
async def test_run_ffmpeg_timeout_kills_process(mock_context, monkeypatch):
    monkeypatch.setattr(webm, "FFMPEG_TIMEOUT_SECONDS", 0.1)
    monkeypatch.setattr(webm, "build_ffmpeg_command", lambda i, o: ["sleep", "5"])
    reporter, _ = make_reporter(mock_context)

    with pytest.raises(webm.ConversionError, match="longer than"):
        await webm.run_ffmpeg("in", "out", reporter)


@pytest.mark.skipif(not FFMPEG_AVAILABLE, reason="ffmpeg not installed")
@pytest.mark.asyncio
async def test_run_ffmpeg_converts_and_reports_progress(tmp_path, mock_context):
    input_path = str(tmp_path / "in.webm")
    output_path = str(tmp_path / "out.mp4")
    # odd dimensions exercise the pad filter
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc=duration=2:size=161x121:rate=10",
            "-c:v",
            "libvpx-vp9",
            input_path,
        ],
        check=True,
    )
    reporter, _ = make_reporter(mock_context)

    await webm.run_ffmpeg(input_path, output_path, reporter)

    assert os.path.getsize(output_path) > 0
    assert reporter.progress == pytest.approx(1.0, abs=0.15)


@pytest.mark.skipif(not FFMPEG_AVAILABLE, reason="ffmpeg not installed")
@pytest.mark.asyncio
async def test_run_ffmpeg_failure_raises(tmp_path, mock_context):
    input_path = tmp_path / "in.webm"
    input_path.write_bytes(b"definitely not a webm")
    reporter, _ = make_reporter(mock_context)

    with pytest.raises(webm.ConversionError):
        await webm.run_ffmpeg(str(input_path), str(tmp_path / "out.mp4"), reporter)
