from fastapi import APIRouter, Request
from starlette.responses import JSONResponse
from loguru import logger
from src import bot
from pydantic import BaseModel

router = APIRouter()


@router.get("/health", response_class=JSONResponse)
async def get_api_health(request: Request):

    response_message = {"health": "ok"}

    return JSONResponse(content=response_message, status_code=200)


class SendMsgParams(BaseModel):
    message_text: str
    chat_id: str


@router.post("/bot/send_msg", response_class=JSONResponse)
async def post_api_bot_send_msg(request: Request, send_msg_params: SendMsgParams):

    logger.info("post_api_bot_send_msg send_msg_params={}", send_msg_params)

    response_message = {
        "message": "Sent message successfully",
    }

    try:

        bot_instance = bot.get_bot_instance()
        if bot_instance is None:
            raise Exception("Failed to get_bot_instance")

        bot_instance.send_message(
            chat_id=send_msg_params.chat_id, text=send_msg_params.message_text
        )

    except Exception as e:

        logger.error("Caught Exception - e={}", e)

        response_message = {
            "error": "Caught exception in post_api_bot_send_msg",
            "error_description": str(e),
        }

        return JSONResponse(content=response_message, status_code=500)

    return JSONResponse(content=response_message, status_code=200)
