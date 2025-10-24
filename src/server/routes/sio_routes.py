import asyncio
from pathlib import Path

from loguru import logger

from src.server import sio

# Store active log streaming tasks
log_streaming_tasks = {}


@sio.on("connect")
async def handle_join(sid, *args, **kwargs):
    logger.info("[sio] user joined sid={}", sid)


@sio.on("command")
async def handle_command(sid, command, *args, **kwargs):
    logger.info("[sio] handle_command command={}", command)


@sio.on("start_log_stream")
async def handle_start_log_stream(sid, *args, **kwargs):
    """Start streaming logs to the client"""
    logger.info("[sio] start_log_stream for sid={}", sid)

    # Cancel existing task if any
    if sid in log_streaming_tasks:
        log_streaming_tasks[sid].cancel()

    # Create new streaming task
    task = asyncio.create_task(stream_logs_to_client(sid))
    log_streaming_tasks[sid] = task


@sio.on("stop_log_stream")
async def handle_stop_log_stream(sid, *args, **kwargs):
    """Stop streaming logs to the client"""
    logger.info("[sio] stop_log_stream for sid={}", sid)

    if sid in log_streaming_tasks:
        log_streaming_tasks[sid].cancel()
        del log_streaming_tasks[sid]


@sio.on("disconnect")
async def handle_disconnect(sid, *args, **kwargs):
    """Clean up when client disconnects"""
    logger.info("[sio] user disconnected sid={}", sid)

    # Cancel streaming task if exists
    if sid in log_streaming_tasks:
        log_streaming_tasks[sid].cancel()
        del log_streaming_tasks[sid]


async def stream_logs_to_client(sid):
    """Stream log file contents to a specific client"""
    log_file_path = Path("../logs/chaddi.log")

    try:
        # Check if log file exists
        if not log_file_path.exists():
            await sio.emit("log_error", {"message": "Log file not found"}, room=sid)
            return

        # Send connection confirmation
        await sio.emit("log_connected", {"message": "Connected to log stream"}, room=sid)

        # Open file and read initial lines
        with open(log_file_path, "r") as file:
            # Read last 100 lines initially
            lines = file.readlines()
            initial_lines = lines[-100:] if len(lines) > 100 else lines

            # Send initial lines
            for line in initial_lines:
                if line.strip():
                    await sio.emit("log_line", {"content": line.rstrip()}, room=sid)
                    await asyncio.sleep(0.01)  # Small delay to avoid overwhelming the client

            # Now tail the file for new lines
            while True:
                line = file.readline()
                if line:
                    await sio.emit("log_line", {"content": line.rstrip()}, room=sid)
                else:
                    # No new line, wait a bit before checking again
                    await asyncio.sleep(0.5)

    except asyncio.CancelledError:
        logger.info("[sio] log streaming cancelled for sid={}", sid)
    except Exception as e:
        logger.error("[sio] error streaming logs for sid={}: {}", sid, e)
        await sio.emit("log_error", {"message": str(e)}, room=sid)
