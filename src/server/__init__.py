import uvicorn
from loguru import logger
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette_exporter import PrometheusMiddleware, handle_metrics
from fastapi_socketio import SocketManager

from src.domain import config, version

# Initialize the config
app_config = config.get_config()

tags_metadata = [
    {
        "name": "api",
        "description": "Chaddi API Endpoints",
    },
    {"name": "ui", "description": "Chaddi Web UI Endpoints"},
]

v = version.get_version()

app = FastAPI(title="chaddi-tg", version=v["git_commit_id"], openapi_tags=tags_metadata)

socket_manager = SocketManager(app=app)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    PrometheusMiddleware,
    app_name="chaddi-tg",
    prefix="http",
    buckets=[0.1, 0.25, 0.5, 0.75, 1],
)
app.add_route("/metrics", handle_metrics)

from src.server.routes import api_routes
from src.server.routes import ui_routes

app.include_router(api_routes.router, prefix="/api", tags=["api"])

app.include_router(ui_routes.router, tags=["ui"])

from src.server.routes import sio_routes


def run_server():

    logger.info(
        "[server] Starting Server on http://localhost:{}",
        app_config.get("SERVER", "PORT"),
    )
    uvicorn.run(
        app,
        host="0.0.0.0",
        log_level="warning",
        port=int(app_config.get("SERVER", "PORT")),
    )
