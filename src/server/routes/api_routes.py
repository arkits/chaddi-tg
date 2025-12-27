import inspect
import json
import math

from cachetools import TTLCache
from fastapi import APIRouter, Request
from loguru import logger
from peewee import DoesNotExist, fn
from playhouse.shortcuts import model_to_dict
from pydantic import BaseModel
from starlette.responses import JSONResponse

from src import bot
from src.db import Bakchod, Group, Message, Quote, group_dao
from src.domain import util

router = APIRouter()

# In-memory cache for dashboard endpoints
# Cache metrics for 60 seconds
metrics_cache = TTLCache(maxsize=1, ttl=60)
# Cache version for 30 seconds (shorter since uptime changes)
version_cache = TTLCache(maxsize=1, ttl=30)


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

        return JSONResponse(content=response_message, status_code=200)

    except Exception as e:
        logger.error("Caught Exception - e={}", e)
        return handle_http_error(str(e), 500)


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

        return JSONResponse(content=response_message, status_code=200)

    except Exception as e:
        logger.error("Caught Exception - e={}", e)
        return handle_http_error(str(e), 500)


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
            raise Exception("Error during json.loads(metadata) :: " + str(e)) from e

        b.metadata = metadata_json
        b.save()

        return JSONResponse(content=response_message, status_code=200)

    except Exception as e:
        logger.error("Caught Exception - e={}", e)
        return handle_http_error(str(e), 500)


class SetGroupMetadataParams(BaseModel):
    group_id: str
    metadata: str


@router.post("/group/metadata", response_class=JSONResponse)
async def post_api_set_group_metadata(
    request: Request, set_group_metadata_params: SetGroupMetadataParams
):
    logger.info(
        "post_api_set_group_metadata set_group_metadata_params={}",
        set_group_metadata_params,
    )

    response_message = {
        "message": "Metadata Updated Successfully",
    }

    try:
        g = Group.get_by_id(set_group_metadata_params.group_id)
        if g is None:
            raise Exception("Unable to find Group")

        # Check if metadata is a JSON
        try:
            metadata_json = json.loads(set_group_metadata_params.metadata)
        except Exception as e:
            raise Exception("Error during json.loads(metadata) :: " + str(e)) from e

        g.metadata = metadata_json
        g.save()

        return JSONResponse(content=response_message, status_code=200)

    except Exception as e:
        logger.error("Caught Exception - e={}", e)
        return handle_http_error(str(e), 500)


@router.get("/quotes", response_class=JSONResponse)
async def get_api_quotes(request: Request, page_number: int = 1):
    items_per_page = 50

    logger.info("get_api_quotes page_number={}", page_number)

    response = {
        "current_page": page_number,
        "total_quotes": 0,
        "total_pages": 0,
        "groups": [],
    }

    try:
        quotes = (
            Quote.select()
            .order_by(Quote.created.desc())
            .paginate(page_number, items_per_page)
            .execute()
        )

        for quote in quotes:
            q = {
                "quote_id": quote.quote_id,
                "created": str(quote.created),
                "text": quote.text,
                "author_bakchod": util.extract_pretty_name_from_bakchod(
                    quote.author_bakchod
                ),
                "quoted_in_group": quote.quoted_in_group.name,
                "quote_capture_bakchod": util.extract_pretty_name_from_bakchod(
                    quote.quote_capture_bakchod
                ),
            }
            response["groups"].append(q)

        response["total_groups"] = Group.select().count()
        response["total_pages"] = response["total_groups"] // items_per_page + 1

        return JSONResponse(content=response, status_code=200)

    except Exception as e:
        logger.error("Caught Exception - e={}", e)
        return handle_http_error(str(e), 500)


@router.get("/quotes/{quote_id}", response_class=JSONResponse)
async def get_api_quote_details(request: Request, quote_id: str = "random"):
    logger.info("get_api_quotes quote_id={}", quote_id)

    try:
        q = None

        if quote_id == "random":
            q = Quote.select().order_by(fn.Random()).get()
        else:
            q = Quote.get_by_id(quote_id)

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

        return JSONResponse(content=response_message, status_code=200)

    except DoesNotExist as e:
        logger.error("Caught DoesNotExist - e={}", e)
        response_message = {
            "error": "Quote does not exist",
        }
        return JSONResponse(content=response_message, status_code=404)

    except Exception as e:
        logger.error("Caught Exception - e={}", e)
        return handle_http_error(str(e), 500)


@router.get("/groups", response_class=JSONResponse)
async def get_api_groups(request: Request, page_number: int = 1):
    items_per_page = 50

    logger.info("get_api_groups page_number={}", page_number)

    response = {
        "current_page": page_number,
        "total_groups": 0,
        "total_pages": 0,
        "groups": [],
    }

    try:
        groups = (
            Group.select()
            .order_by(Group.updated.desc())
            .paginate(page_number, items_per_page)
            .execute()
        )

        for group in groups:
            g = {
                "group_id": group.group_id,
                "name": group.name,
                "created": str(group.created),
                "updated": str(group.updated),
            }
            response["groups"].append(g)

        response["total_groups"] = Group.select().count()
        response["total_pages"] = response["total_groups"] // items_per_page + 1

        return JSONResponse(content=response, status_code=200)

    except Exception as e:
        logger.error("Caught Exception - e={}", e)
        return handle_http_error(str(e), 500)


@router.get("/groups/{group_id}", response_class=JSONResponse)
async def get_api_group_details(request: Request, group_id):
    response = {}

    try:
        if group_id is None:
            raise Exception("group_id was None")

        g = Group.get_by_id(group_id)
        response = json.loads(json.dumps(model_to_dict(g), sort_keys=True, default=str))

        return JSONResponse(content=response, status_code=200)

    except Exception as e:
        logger.error("Caught Exception - e={}", e)
        return handle_http_error(str(e), 500)


@router.get("/groups/{group_id}/messages", response_class=JSONResponse)
async def get_api_group_messages(
    request: Request, group_id, page_number: int = 1, include_update: bool = False
):
    try:
        items_per_page = 50

        if group_id is None:
            raise Exception("group_id was None")

        group = None

        try:
            group = Group.get_by_id(group_id)
        except Exception as e:
            logger.error("Caught Exception - e={}", e)

        if group is None:
            raise Exception("Group not found")

        total_messages = Message.select().where(Message.to_id == group_id).count()

        total_pages = total_messages // items_per_page + 1

        messages = group_dao.get_all_messages_by_group_id(
            group_id, page_number, items_per_page
        )

        response = {
            "current_page": page_number,
            "total_pages": total_pages,
            "total_messages": total_messages,
            "messages": [],
        }

        for message in messages:
            m = {
                "message_id": message.message_id,
                "text": message.text,
                "time_sent": str(message.time_sent),
                "from_bakchod": {
                    "tg_id": message.from_bakchod.tg_id,
                    "username": message.from_bakchod.username,
                    "pretty_name": message.from_bakchod.pretty_name,
                },
            }
            if include_update:
                m["update"] = json.dumps(message.update)
            response["messages"].append(m)

        return JSONResponse(content=response, status_code=200)

    except Exception as e:
        logger.error("Caught Exception - e={}", e)
        return handle_http_error(str(e), 500)


@router.get("/bakchods", response_class=JSONResponse)
async def get_api_bakchods(request: Request, page_number: int = 1):
    items_per_page = 50

    logger.info("get_api_bakchods page_number={}", page_number)

    response = {
        "current_page": page_number,
        "total_bakchods": 0,
        "total_pages": 0,
        "bakchods": [],
    }

    try:
        bakchods = (
            Bakchod.select()
            .order_by(Bakchod.updated.desc())
            .paginate(page_number, items_per_page)
            .execute()
        )

        for bakchod in bakchods:
            response["bakchods"].append(quick_model_to_dict(bakchod))

        response["total_bakchods"] = Bakchod.select().count()
        response["total_pages"] = response["total_bakchods"] // items_per_page + 1

        return JSONResponse(content=response, status_code=200)

    except Exception as e:
        logger.error("Caught Exception - e={}", e)
        return handle_http_error(str(e), 500)


@router.get("/bakchods/{tg_id}", response_class=JSONResponse)
async def get_api_bakchod_details(request: Request, tg_id):
    try:
        if tg_id is None:
            raise Exception("tg_id was None")

        try:
            b = Bakchod.get_by_id(tg_id)
            response = quick_model_to_dict(b)
            return JSONResponse(content=response, status_code=200)

        except Exception:
            raise Exception("Bakchod not found") from None

    except Exception as e:
        logger.error("Caught Exception - e={}", e)
        return handle_http_error(str(e), 500)


def quick_model_to_dict(model):
    return json.loads(json.dumps(model_to_dict(model), sort_keys=True, default=str))


def _compute_dashboard_metrics():
    """Compute dashboard metrics (used for caching)"""
    from datetime import datetime, timedelta

    bakchods_count = Bakchod.select().count()
    groups_count = Group.select().count()
    messages_count = Message.select().count()
    quotes_count = Quote.select().count()

    from src.db import Roll, ScheduledJob

    roll_count = Roll.select().count()
    jobs_count = ScheduledJob.select().count()

    # Get recent activity stats (last 24 hours)
    last_24h = datetime.now() - timedelta(hours=24)
    recent_messages = Message.select().where(Message.time_sent >= last_24h).count()
    recent_bakchods = Bakchod.select().where(Bakchod.lastseen >= last_24h).count()

    return {
        "bakchods_count": bakchods_count,
        "groups_count": groups_count,
        "messages_count": messages_count,
        "quotes_count": quotes_count,
        "roll_count": roll_count,
        "jobs_count": jobs_count,
        "recent_messages": recent_messages,
        "recent_bakchods": recent_bakchods,
    }


@router.get("/dashboard/metrics", response_class=JSONResponse)
async def get_dashboard_metrics(request: Request):
    """Get basic dashboard metrics"""
    try:
        cache_key = "metrics"
        if cache_key not in metrics_cache:
            metrics_cache[cache_key] = _compute_dashboard_metrics()

        response = metrics_cache[cache_key]
        return JSONResponse(content=response, status_code=200)

    except Exception as e:
        logger.error("Caught Exception - e={}", e)
        return handle_http_error(str(e), 500)


@router.get("/dashboard/activity", response_class=JSONResponse)
async def get_dashboard_activity(request: Request):
    """Get most active users and groups"""
    try:
        # Get most active bakchod
        most_active_bakchod = (
            Bakchod.select(Bakchod, fn.COUNT(Message.id).alias("msg_count"))
            .join(Message, on=(Message.from_bakchod == Bakchod.tg_id))
            .group_by(Bakchod)
            .order_by(fn.COUNT(Message.id).desc())
            .first()
        )

        # Get most active group
        most_active_group = (
            Group.select(Group, fn.COUNT(Message.id).alias("msg_count"))
            .join(Message, on=(Message.to_id == Group.group_id))
            .group_by(Group)
            .order_by(fn.COUNT(Message.id).desc())
            .first()
        )

        # Get latest message timestamp
        latest_message = Message.select().order_by(Message.time_sent.desc()).first()

        response = {
            "most_active_bakchod": (
                {
                    "pretty_name": (
                        most_active_bakchod.pretty_name if most_active_bakchod else None
                    ),
                    "username": (
                        most_active_bakchod.username if most_active_bakchod else None
                    ),
                }
                if most_active_bakchod
                else None
            ),
            "most_active_group": (
                {
                    "name": most_active_group.name if most_active_group else None,
                }
                if most_active_group
                else None
            ),
            "latest_message_time": (
                str(latest_message.time_sent) if latest_message else None
            ),
        }

        return JSONResponse(content=response, status_code=200)

    except Exception as e:
        logger.error("Caught Exception - e={}", e)
        return handle_http_error(str(e), 500)


@router.get("/dashboard/random-quote", response_class=JSONResponse)
async def get_dashboard_random_quote(request: Request):
    """Get a random quote"""
    try:
        random_quote = Quote.select().order_by(fn.Random()).first()

        if not random_quote:
            return JSONResponse(content={"quote": None}, status_code=200)

        response = {
            "quote": {
                "text": random_quote.text,
                "created": str(random_quote.created),
                "author_bakchod": {
                    "pretty_name": random_quote.author_bakchod.pretty_name,
                    "username": random_quote.author_bakchod.username,
                },
                "quoted_in_group": {
                    "name": random_quote.quoted_in_group.name,
                },
            }
        }

        return JSONResponse(content=response, status_code=200)

    except Exception as e:
        logger.error("Caught Exception - e={}", e)
        return handle_http_error(str(e), 500)


def _compute_dashboard_version():
    """Compute dashboard version info (used for caching)"""
    from src.domain import version

    v = version.get_version()

    return {
        "semver": str(v["semver"]) if v.get("semver") else "unknown",
        "git_commit_id": (
            str(v["git_commit_id"]) if v.get("git_commit_id") else "unknown"
        ),
        "git_commit_time": (
            str(v["git_commit_time"]) if v.get("git_commit_time") else "unknown"
        ),
        "pretty_uptime": (
            str(v["pretty_uptime"]) if v.get("pretty_uptime") else "unknown"
        ),
    }


@router.get("/dashboard/version", response_class=JSONResponse)
async def get_dashboard_version(request: Request):
    """Get version information"""
    try:
        cache_key = "version"
        if cache_key not in version_cache:
            version_cache[cache_key] = _compute_dashboard_version()

        response = version_cache[cache_key]
        return JSONResponse(content=response, status_code=200)

    except Exception as e:
        logger.error("Caught Exception - e={}", e)
        return handle_http_error(str(e), 500)


def handle_http_error(error_description, status_code):
    error_response = {
        "error": f"Caught fatal exception in {inspect.stack()[1][3]}",
        "error_description": error_description,
    }

    return JSONResponse(content=error_response, status_code=status_code)
