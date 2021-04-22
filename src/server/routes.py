from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from db import Bakchod, Group, Message

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
