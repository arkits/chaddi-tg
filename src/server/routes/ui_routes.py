import json
import locale
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.db import (
    Bakchod,
    Group,
    GroupMember,
    Message,
    Quote,
    Roll,
    ScheduledJob,
    group_dao,
)
from loguru import logger
from src import bot
from src.domain import version

router = APIRouter()

templates = Jinja2Templates(directory="templates")

locale.setlocale(locale.LC_ALL, "en_US")


def to_pretty_json(value):
    return json.dumps(value, sort_keys=True, indent=4, separators=(",", ": "))


def to_pretty_number(value):
    return locale.format_string("%d", value, grouping=True)


templates.env.filters["tojson_pretty"] = to_pretty_json
templates.env.filters["tonumber_pretty"] = to_pretty_number


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):

    bakchods_count = Bakchod.select().count()
    groups_count = Group.select().count()
    messages_count = Message.select().count()
    quotes_count = Quote.select().count()
    roll_count = Roll.select().count()

    v = version.get_version()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "bakchods_count": bakchods_count,
            "groups_count": groups_count,
            "messages_count": messages_count,
            "quotes_count": quotes_count,
            "roll_count": roll_count,
            "version_info": v,
        },
    )


@router.get("/bakchods", response_class=HTMLResponse)
async def get_bakchods(request: Request):

    bakchods = Bakchod.select().order_by(Bakchod.lastseen.desc()).limit(100)
    bakchods_count = Bakchod.select().count()

    return templates.TemplateResponse(
        "bakchods.html",
        {"request": request, "bakchods": bakchods, "bakchods_count": bakchods_count},
    )


@router.get("/groups", response_class=HTMLResponse)
async def get_groups(request: Request):

    groups = Group.select().order_by(Group.updated.desc())
    groups_count = Group.select().count()

    return templates.TemplateResponse(
        "groups.html",
        {"request": request, "groups": groups, "groups_count": groups_count},
    )


@router.get("/messages", response_class=HTMLResponse)
async def get_groups(request: Request):

    # Get the last X messages
    messages = Message.select().limit(100).order_by(Message.time_sent.desc())

    return templates.TemplateResponse(
        "messages.html", {"request": request, "messages": messages}
    )


@router.get("/details/bakchod", response_class=HTMLResponse)
async def get_details_bakchod(request: Request, tg_id: str = "unset"):

    b = Bakchod.get_by_id(tg_id)

    groupmember_rows = GroupMember.select().where(GroupMember.bakchod == b.tg_id)

    bakchod_groups = []

    for groupmember_row in groupmember_rows:
        group_row = Group.get_by_id(groupmember_row.group)
        bakchod_groups.append(group_row)

    return templates.TemplateResponse(
        "details_bakchod.html",
        {"request": request, "bakchod": b, "groups": bakchod_groups},
    )


@router.get("/details/group", response_class=HTMLResponse)
async def get_details_group(request: Request, group_id: str = "unset"):

    g = Group.get_by_id(group_id)

    message_count = Message.select().where(Message.to_id == group_id).count()

    groupmembers = group_dao.get_all_groupmembers_by_group_id(group_id)

    return templates.TemplateResponse(
        "details_group.html",
        {
            "request": request,
            "group": g,
            "message_count": message_count,
            "groupmembers": groupmembers,
        },
    )


@router.get("/details/messages", response_class=HTMLResponse)
async def get_details_group_messages(
    request: Request, group_id: str = "unset", page: int = 1, limit: int = 100
):

    # define upper limit on limit as 250
    if limit > 250:
        limit = 250

    g = Group.get_by_id(group_id)

    message_count = Message.select().where(Message.to_id == group_id).count()

    messages = group_dao.get_all_messages_by_group_id(group_id, page, limit)

    number_of_pages = message_count // limit + 1

    return templates.TemplateResponse(
        "details_group_messages.html",
        {
            "request": request,
            "group": g,
            "messages": messages,
            "message_count": message_count,
            "page": page,
            "limit": limit,
            "number_of_pages": number_of_pages,
        },
    )


@router.get("/quotes", response_class=HTMLResponse)
async def get_groups(request: Request):

    quotes = Quote.select().limit(100).order_by(Quote.created.desc())
    quotes_count = Quote.select().count()

    return templates.TemplateResponse(
        "quotes.html",
        {"request": request, "quotes": quotes, "quotes_count": quotes_count},
    )


@router.post("/api/bot/send_message", response_class=HTMLResponse)
async def post_api_bot_send_message(
    request: Request, message: str = Form("unset"), group_id: str = Form("unset")
):

    logger.info("post_api_bot_send_message group_id={} message={}", group_id, message)

    response_message = {
        "title": "Success",
        "message": "Sent message successfully",
        "alert_type": "alert-success",  # alert-success, alert-danger
    }

    g = None

    try:

        if group_id == "unset":
            raise Exception("group_id was unset")

        if message == "unset":
            raise Exception("message was unset")

        bot_instance = bot.get_bot_instance()
        if bot_instance is None:
            raise Exception("Failed to get_bot_instance")

        bot_instance.send_message(chat_id=group_id, text=message)

        g = Group.get_by_id(group_id)

    except Exception as e:

        logger.error("Caught Exception - e={}", e)

        response_message["title"] = "Backend Error"
        response_message["message"] = e
        response_message["alert_type"] = "alert-danger"

        return templates.TemplateResponse(
            "details_group.html",
            {
                "request": request,
                "group": g,
                "response_message": response_message,
            },
        )

    return templates.TemplateResponse(
        "details_group.html",
        {"request": request, "group": g, "response_message": response_message},
    )


@router.get("/jobs", response_class=HTMLResponse)
async def get_jobs(request: Request):

    jobs = ScheduledJob.select().limit(100).order_by(ScheduledJob.created.desc())
    job_count = ScheduledJob.select().count()

    return templates.TemplateResponse(
        "jobs.html",
        {"request": request, "jobs": jobs, "job_count": job_count},
    )