from loguru import logger

from src.server import sio


@sio.on("connect")
async def handle_join(sid, *args, **kwargs):
    logger.info("[sio] user joined sid={}", sid)


@sio.on("command")
async def handle_command(sid, command, *args, **kwargs):
    logger.info("[sio] handle_command command={}", command)
