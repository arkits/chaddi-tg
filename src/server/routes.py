from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.db import Bakchod, Group, Message, Quote, group
from loguru import logger

router = APIRouter()

templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/bakchods", response_class=HTMLResponse)
async def get_bakchods(request: Request):

    bakchods = Bakchod.select()

    return templates.TemplateResponse(
        "bakchods.html", {"request": request, "bakchods": bakchods}
    )


@router.get("/groups", response_class=HTMLResponse)
async def get_groups(request: Request):

    groups = Group.select()

    return templates.TemplateResponse(
        "groups.html", {"request": request, "groups": groups}
    )


@router.get("/messages", response_class=HTMLResponse)
async def get_groups(request: Request):

    # Get the last X messages
    messages = Message.select().limit(100).order_by(Message.time_sent.desc())

    return templates.TemplateResponse(
        "messages.html", {"request": request, "messages": messages}
    )


@router.get("/details/group", response_class=HTMLResponse)
async def get_details_group(request: Request, group_id: str = "unset"):

    g = Group.get_by_id(group_id)

    return templates.TemplateResponse(
        "details_group.html", {"request": request, "group": g}
    )


@router.get("/details/members", response_class=HTMLResponse)
async def get_details_group_members(request: Request, group_id: str = "unset"):

    g = Group.get_by_id(group_id)

    groupmembers = group.get_all_groupmembers_by_group_id(group_id)

    return templates.TemplateResponse(
        "details_group_members.html",
        {"request": request, "group": g, "groupmembers": groupmembers},
    )


@router.get("/details/messages", response_class=HTMLResponse)
async def get_details_group_messages(request: Request, group_id: str = "unset"):

    g = Group.get_by_id(group_id)

    message_count = Message.select().count()

    messages = group.get_all_messages_by_group_id(group_id, 100)

    return templates.TemplateResponse(
        "details_group_messages.html",
        {
            "request": request,
            "group": g,
            "messages": messages,
            "message_count": message_count,
        },
    )


@router.get("/quotes", response_class=HTMLResponse)
async def get_groups(request: Request):

    # Get the last X messages
    quotes = Quote.select().limit(100).order_by(Quote.created.desc())

    return templates.TemplateResponse(
        "quotes.html", {"request": request, "quotes": quotes}
    )