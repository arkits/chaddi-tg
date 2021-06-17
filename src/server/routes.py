import json
from fastapi import APIRouter, Request, Form
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


@router.get("/details/bakchod", response_class=HTMLResponse)
async def get_details_group(request: Request, tg_id: str = "unset"):

    b = Bakchod.get_by_id(tg_id)

    return templates.TemplateResponse(
        "details_bakchod.html", {"request": request, "bakchod": b}
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


@router.post("/api/bakchod/metadata", response_class=HTMLResponse)
async def post_update_bakchod_metadata(
    request: Request, metadata: str = Form("unset"), tg_id: str = Form("unset")
):

    logger.info("post_update_bakchod_metadata tg_id={} metadata={}", tg_id, metadata)

    response_message = {
        "title": "Success",
        "message": "Metadata updated successfully",
        "alert_type": "alert-success",  # alert-success, alert-danger
    }

    try:

        if tg_id == "unset":
            raise Exception("tg_id was unset")

        if metadata == "unset":
            raise Exception("metadata was unset")

        # Check if metadata is a JSON
        try:
            json.loads(metadata)
        except Exception as e:
            raise Exception("Error during json.loads(metadata) :: " + str(e))

        b = Bakchod.get_by_id(tg_id)
        if b is None:
            raise Exception("Unable to find Bakchod")

        b.metadata = metadata
        b.save()

    except Exception as e:

        logger.error("Caught Exception - e={}", e)

        response_message["title"] = "Backend Error"
        response_message["message"] = e
        response_message["alert_type"] = "alert-danger"

        return templates.TemplateResponse(
            "details_bakchod.html",
            {
                "request": request,
                "bakchod": None,
                "response_message": response_message,
            },
        )

    return templates.TemplateResponse(
        "details_bakchod.html",
        {"request": request, "bakchod": b, "response_message": response_message},
    )
