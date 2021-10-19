import json
import math

from peewee import DoesNotExist, fn
from src.db import Bakchod, Quote
from fastapi import APIRouter, Request
from starlette.responses import JSONResponse
from loguru import logger
from src import bot
from pydantic import BaseModel

from src.domain import util

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


class SetBakchodRokdaParams(BaseModel):
    bakchod_id: str
    rokda: str


@router.post("/bakchod/rokda", response_class=JSONResponse)
async def post_api_set_bakchod_rokda(
    request: Request, set_bakchod_rokda_params: SetBakchodRokdaParams
):

    logger.info(
        "post_api_set_bakchod_rokda set_bakchod_rokda_params={}",
        set_bakchod_rokda_params,
    )

    response_message = {
        "message": "Rokda Updated Successfully",
    }

    try:

        b = Bakchod.get_by_id(set_bakchod_rokda_params.bakchod_id)
        if b is None:
            raise Exception("Unable to find Bakchod")

        rokda_to_set = float(set_bakchod_rokda_params.rokda)

        if not math.isfinite(rokda_to_set):
            raise Exception("Bad params: rokda")

        b.rokda = rokda_to_set
        b.save()

    except Exception as e:

        logger.error("Caught Exception - e={}", e)

        response_message = {
            "error": "Caught exception in post_api_set_bakchod_rokda",
            "error_description": str(e),
        }

        return JSONResponse(content=response_message, status_code=500)

    return JSONResponse(content=response_message, status_code=200)


class SetBakchodMetadataParams(BaseModel):
    bakchod_id: str
    metadata: str


@router.post("/bakchod/metadata", response_class=JSONResponse)
async def post_api_set_bakchod_metadata(
    request: Request, set_bakchod_metadata_params: SetBakchodMetadataParams
):

    logger.info(
        "post_api_set_bakchod_metadata set_bakchod_metadata_params={}",
        set_bakchod_metadata_params,
    )

    response_message = {
        "message": "Metadata Updated Successfully",
    }

    try:

        b = Bakchod.get_by_id(set_bakchod_metadata_params.bakchod_id)
        if b is None:
            raise Exception("Unable to find Bakchod")

        # Check if metadata is a JSON
        try:
            metadata_json = json.loads(set_bakchod_metadata_params.metadata)
        except Exception as e:
            raise Exception("Error during json.loads(metadata) :: " + str(e))

        b.metadata = metadata_json
        b.save()

    except Exception as e:

        logger.error("Caught Exception - e={}", e)

        response_message = {
            "error": "Caught exception in post_api_set_bakchod_metadata",
            "error_description": str(e),
        }

        return JSONResponse(content=response_message, status_code=500)

    return JSONResponse(content=response_message, status_code=200)


@router.get("/quotes", response_class=JSONResponse)
async def get_api_quotes(request: Request, id: str = "unset"):

    logger.info(
        "get_api_quotes id={}",
        id,
    )

    try:

        if id == "unset":

            q = Quote.select().order_by(fn.Random()).get()

        else:

            q = Quote.get_by_id(id)

        response_message = {
            "quote_id": q.quote_id,
            "created": str(q.created),
            "text": q.text,
            "author_bakchod": util.extract_pretty_name_from_bakchod(q.author_bakchod),
            "quoted_in_group": q.quoted_in_group.name,
            "quote_capture_bakchod": util.extract_pretty_name_from_bakchod(
                q.quote_capture_bakchod
            ),
        }

        logger.debug("Generated response_message={}", response_message)

    except DoesNotExist as e:

        logger.error("Caught DoesNotExist - e={}", e)

        response_message = {
            "error": "Quote does not exist",
        }

        return JSONResponse(content=response_message, status_code=404)

    except Exception as e:

        logger.error("Caught Exception - e={}", e)

        response_message = {
            "error": "Caught exception in get_api_quotes",
            "error_description": str(e),
        }

        return JSONResponse(content=response_message, status_code=500)

    return JSONResponse(content=response_message, status_code=200)