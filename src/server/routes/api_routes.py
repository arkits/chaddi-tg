import inspect
import json
import math

from cachetools import TTLCache
from fastapi import APIRouter, Request
from loguru import logger
from peewee import SQL, DoesNotExist, fn
from playhouse.shortcuts import model_to_dict
from pydantic import BaseModel
from starlette.responses import JSONResponse

from src import bot
from src.db import (
    Bakchod,
    CommandUsage,
    Group,
    GroupMember,
    Message,
    Quote,
    ScheduledJob,
    group_dao,
)
from src.domain import util

router = APIRouter()

# In-memory cache for dashboard endpoints
# Cache metrics for 60 seconds
metrics_cache = TTLCache(maxsize=1, ttl=60)
# Cache version for 30 seconds (shorter since uptime changes)
version_cache = TTLCache(maxsize=1, ttl=30)
# Cache command stats for 60 seconds
commands_stats_cache = TTLCache(maxsize=1, ttl=60)
# Cache command aggregations for 60 seconds
commands_agg_cache = TTLCache(maxsize=10, ttl=60)
# Cache hourly distribution for 60 seconds
commands_hourly_cache = TTLCache(maxsize=1, ttl=60)
# Cache recent command executions for 30 seconds
commands_recent_cache = TTLCache(maxsize=10, ttl=30)


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
                "author_bakchod": util.extract_pretty_name_from_bakchod(quote.author_bakchod),
                "quoted_in_group": quote.quoted_in_group.name,
                "quote_capture_bakchod": util.extract_pretty_name_from_bakchod(
                    quote.quote_capture_bakchod
                ),
            }
            response["groups"].append(q)

        response["total_quotes"] = Quote.select().count()
        response["total_pages"] = math.ceil(response["total_quotes"] / items_per_page)

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
            "quote_capture_bakchod": util.extract_pretty_name_from_bakchod(q.quote_capture_bakchod),
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
        response["total_pages"] = math.ceil(response["total_groups"] / items_per_page)

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


@router.get("/groups/{group_id}/members", response_class=JSONResponse)
async def get_api_group_members(request: Request, group_id):
    try:
        if group_id is None:
            raise Exception("group_id was None")

        try:
            Group.get_by_id(group_id)
        except DoesNotExist as e:
            raise Exception("Group not found") from e

        groupmembers = group_dao.get_all_groupmembers_by_group_id(group_id)

        members = []
        for groupmember in groupmembers:
            bakchod = groupmember.bakchod
            members.append(
                {
                    "tg_id": bakchod.tg_id,
                    "username": bakchod.username,
                    "pretty_name": bakchod.pretty_name,
                    "rokda": bakchod.rokda,
                    "lastseen": str(bakchod.lastseen) if bakchod.lastseen else None,
                }
            )

        return JSONResponse(
            content={"members": members, "total": len(members)},
            status_code=200,
        )

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

        total_pages = math.ceil(total_messages / items_per_page)

        messages = group_dao.get_all_messages_by_group_id(group_id, page_number, items_per_page)

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
        response["total_pages"] = math.ceil(response["total_bakchods"] / items_per_page)

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
    last_24h = datetime.utcnow() - timedelta(hours=24)
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
                    "username": (most_active_bakchod.username if most_active_bakchod else None),
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
            "latest_message_time": (str(latest_message.time_sent) if latest_message else None),
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
        "git_commit_id": (str(v["git_commit_id"]) if v.get("git_commit_id") else "unknown"),
        "git_commit_time": (str(v["git_commit_time"]) if v.get("git_commit_time") else "unknown"),
        "pretty_uptime": (str(v["pretty_uptime"]) if v.get("pretty_uptime") else "unknown"),
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


@router.get("/jobs", response_class=JSONResponse)
async def get_api_jobs(request: Request, page_number: int = 1):
    items_per_page = 50

    logger.info("get_api_jobs page_number={}", page_number)

    response = {
        "current_page": page_number,
        "total_jobs": 0,
        "total_pages": 0,
        "jobs": [],
    }

    try:
        jobs = (
            ScheduledJob.select()
            .order_by(ScheduledJob.created.desc())
            .paginate(page_number, items_per_page)
            .execute()
        )

        for job in jobs:
            j = {
                "job_id": job.job_id,
                "created": str(job.created),
                "updated": str(job.updated),
                "from_bakchod": util.extract_pretty_name_from_bakchod(job.from_bakchod),
                "group": job.group.name if job.group else None,
                "job_context": job.job_context,
            }
            response["jobs"].append(j)

        response["total_jobs"] = ScheduledJob.select().count()
        response["total_pages"] = math.ceil(response["total_jobs"] / items_per_page)

        return JSONResponse(content=response, status_code=200)

    except Exception as e:
        logger.error("Caught Exception - e={}", e)
        return handle_http_error(str(e), 500)


@router.get("/commands/stats", response_class=JSONResponse)
async def get_api_commands_stats(request: Request):
    logger.info("get_api_commands_stats")

    try:
        cache_key = "stats"
        if cache_key not in commands_stats_cache:
            commands_stats_cache[cache_key] = _compute_commands_stats()

        return JSONResponse(content=commands_stats_cache[cache_key], status_code=200)

    except Exception as e:
        logger.error("Caught Exception - e={}", e)
        return handle_http_error(str(e), 500)


def _compute_commands_stats():
    from datetime import datetime, timedelta

    total_commands = CommandUsage.select().count()

    last_24h = datetime.utcnow() - timedelta(hours=24)
    recent_commands = CommandUsage.select().where(CommandUsage.executed_at >= last_24h).count()

    last_7d = datetime.utcnow() - timedelta(days=7)
    weekly_commands = CommandUsage.select().where(CommandUsage.executed_at >= last_7d).count()

    return {
        "total": total_commands,
        "last_24h": recent_commands,
        "last_7d": weekly_commands,
    }


@router.get("/commands/top", response_class=JSONResponse)
async def get_api_commands_top(request: Request, limit: int = 10):
    logger.info("get_api_commands_top limit={}", limit)

    try:
        cache_key = f"top_{limit}"
        if cache_key not in commands_agg_cache:
            commands_agg_cache[cache_key] = _compute_commands_top(limit)

        return JSONResponse(content=commands_agg_cache[cache_key], status_code=200)

    except Exception as e:
        logger.error("Caught Exception - e={}", e)
        return handle_http_error(str(e), 500)


def _compute_commands_top(limit: int):
    top_commands_query = (
        CommandUsage.select(CommandUsage.command_name, fn.COUNT(CommandUsage.id).alias("count"))
        .group_by(CommandUsage.command_name)
        .order_by(fn.COUNT(CommandUsage.id).desc())
        .limit(limit)
    )

    return [{"command_name": row.command_name, "count": row.count} for row in top_commands_query]


@router.get("/commands/by-group", response_class=JSONResponse)
async def get_api_commands_by_group(request: Request, limit: int = 10):
    logger.info("get_api_commands_by_group limit={}", limit)

    try:
        cache_key = f"by_group_{limit}"
        if cache_key not in commands_agg_cache:
            commands_agg_cache[cache_key] = _compute_commands_by_group(limit)

        return JSONResponse(content=commands_agg_cache[cache_key], status_code=200)

    except Exception as e:
        logger.error("Caught Exception - e={}", e)
        return handle_http_error(str(e), 500)


def _compute_commands_by_group(limit: int):
    commands_by_group_query = (
        CommandUsage.select(Group.name, fn.COUNT(CommandUsage.id).alias("count"))
        .join(Group, on=(CommandUsage.group == Group.group_id))
        .group_by(Group.name)
        .order_by(fn.COUNT(CommandUsage.id).desc())
        .limit(limit)
    )

    return [{"name": row.name, "count": row.count} for row in commands_by_group_query]


@router.get("/commands/by-user", response_class=JSONResponse)
async def get_api_commands_by_user(request: Request, limit: int = 10):
    logger.info("get_api_commands_by_user limit={}", limit)

    try:
        cache_key = f"by_user_{limit}"
        if cache_key not in commands_agg_cache:
            commands_agg_cache[cache_key] = _compute_commands_by_user(limit)

        return JSONResponse(content=commands_agg_cache[cache_key], status_code=200)

    except Exception as e:
        logger.error("Caught Exception - e={}", e)
        return handle_http_error(str(e), 500)


def _compute_commands_by_user(limit: int):
    commands_by_user_query = (
        Bakchod.select(
            Bakchod.pretty_name, Bakchod.username, fn.COUNT(CommandUsage.id).alias("count")
        )
        .join(CommandUsage, on=(CommandUsage.from_bakchod == Bakchod.tg_id))
        .where(Bakchod.pretty_name.is_null(False))
        .group_by(Bakchod.pretty_name, Bakchod.username)
        .order_by(fn.COUNT(CommandUsage.id).desc())
        .limit(limit)
    )

    return [
        {"pretty_name": row.pretty_name, "username": row.username, "count": row.count}
        for row in commands_by_user_query
    ]


@router.get("/commands/hourly", response_class=JSONResponse)
async def get_api_commands_hourly(request: Request):
    logger.info("get_api_commands_hourly")

    try:
        cache_key = "hourly"
        if cache_key not in commands_hourly_cache:
            commands_hourly_cache[cache_key] = _compute_commands_hourly()

        return JSONResponse(content=commands_hourly_cache[cache_key], status_code=200)

    except Exception as e:
        logger.error("Caught Exception - e={}", e)
        return handle_http_error(str(e), 500)


def _compute_commands_hourly():
    from datetime import datetime, timedelta

    last_24h = datetime.utcnow() - timedelta(hours=24)

    hourly_counts = (
        CommandUsage.select(
            fn.to_char(CommandUsage.executed_at, "HH24").alias("hour"),
            fn.COUNT(CommandUsage.id).alias("count"),
        )
        .where(CommandUsage.executed_at >= last_24h)
        .group_by(SQL("hour"))
        .order_by(SQL("hour"))
    )

    count_map = {row.hour: row.count for row in hourly_counts}

    hourly_data = []
    for i in range(24):
        hour_start = datetime.utcnow() - timedelta(hours=i + 1)
        hour_str = hour_start.strftime("%H")
        hourly_data.insert(
            0, {"hour": hour_start.strftime("%H:00"), "count": count_map.get(hour_str, 0)}
        )

    return hourly_data


@router.get("/commands/recent", response_class=JSONResponse)
async def get_api_commands_recent(request: Request, limit: int = 50):
    logger.info("get_api_commands_recent limit={}", limit)

    try:
        cache_key = f"recent_{limit}"
        if cache_key not in commands_recent_cache:
            commands_recent_cache[cache_key] = _compute_commands_recent(limit)

        return JSONResponse(content=commands_recent_cache[cache_key], status_code=200)

    except Exception as e:
        logger.error("Caught Exception - e={}", e)
        return handle_http_error(str(e), 500)


def _compute_commands_recent(limit: int):
    recent_executions = (
        CommandUsage.select().order_by(CommandUsage.executed_at.desc()).limit(limit).execute()
    )

    commands = []
    for cmd in recent_executions:
        c = {
            "id": cmd.id,
            "command_name": cmd.command_name,
            "executed_at": str(cmd.executed_at),
            "from_bakchod": (
                util.extract_pretty_name_from_bakchod(cmd.from_bakchod)
                if cmd.from_bakchod
                else None
            ),
            "group": cmd.group.name if cmd.group else None,
        }
        commands.append(c)

    return commands


class SendMessageToGroupParams(BaseModel):
    message: str


@router.post("/groups/{group_id}/send-message", response_class=JSONResponse)
async def post_api_group_send_message(
    request: Request, group_id: str, params: SendMessageToGroupParams
):
    logger.info("post_api_group_send_message group_id={} message={}", group_id, params.message)

    try:
        g = Group.get_by_id(group_id)
        if g is None:
            raise Exception("Group not found")

        bot_instance = bot.get_bot_instance()
        if bot_instance is None:
            raise Exception("Failed to get_bot_instance")

        bot_instance.send_message(chat_id=group_id, text=params.message)

        return JSONResponse(content={"message": "Sent message successfully"}, status_code=200)

    except Exception as e:
        logger.error("Caught Exception - e={}", e)
        return handle_http_error(str(e), 500)


@router.get("/bakchods/{tg_id}/groups", response_class=JSONResponse)
async def get_api_bakchod_groups(request: Request, tg_id: str):
    logger.info("get_api_bakchod_groups tg_id={}", tg_id)

    try:
        b = Bakchod.get_by_id(tg_id)
        if b is None:
            raise Exception("Bakchod not found")

        groupmember_rows = (
            GroupMember.select(Group)
            .join(Group, on=(GroupMember.group == Group.group_id))
            .where(GroupMember.bakchod == b.tg_id)
        )

        groups = []
        for group_row in groupmember_rows:
            groups.append(
                {
                    "group_id": group_row.group_id,
                    "name": group_row.name,
                    "created": str(group_row.created),
                    "updated": str(group_row.updated),
                }
            )

        return JSONResponse(content=groups, status_code=200)

    except Exception as e:
        logger.error("Caught Exception - e={}", e)
        return handle_http_error(str(e), 500)


def handle_http_error(error_description, status_code):
    error_response = {
        "error": f"Caught fatal exception in {inspect.stack()[1][3]}",
        "error_description": error_description,
    }

    return JSONResponse(content=error_response, status_code=status_code)
