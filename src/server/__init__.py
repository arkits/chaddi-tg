import asyncio

import sentry_sdk
import socketio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger
from starlette_exporter import PrometheusMiddleware, handle_metrics

from src.domain import config, version
from src.server.routes import api_routes, ui_routes

# Initialize Sentry SDK before FastAPI app
sentry_sdk.init(
    dsn="https://b28179ae59e491947ce4cb052ab4c3fc@o425745.ingest.us.sentry.io/4510605721141248",
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    # Set profile_session_sample_rate to 1.0 to profile 100%
    # of profile sessions.
    profile_session_sample_rate=1.0,
    # Set profile_lifecycle to "trace" to automatically
    # run the profiler on when there is an active transaction
    profile_lifecycle="trace",
)

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

fastapi_app = FastAPI(title="chaddi-tg", version=v["git_commit_id"], openapi_tags=tags_metadata)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

fastapi_app.add_middleware(GZipMiddleware, minimum_size=1000)

fastapi_app.add_middleware(
    PrometheusMiddleware,
    app_name="chaddi-tg",
    prefix="http",
    buckets=[0.1, 0.25, 0.5, 0.75, 1],
)
fastapi_app.add_route("/metrics", handle_metrics)

fastapi_app.mount("/static", StaticFiles(directory="static"), name="static")

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    # logger=True,
    # engineio_logger=True
)

# Attach sio to fastapi_app for use in route handlers
fastapi_app.sio = sio

fastapi_app.include_router(api_routes.router, prefix="/api", tags=["api"])

fastapi_app.include_router(ui_routes.router, tags=["ui"])

# Import sio_routes after sio is defined so handlers can register
from src.server.routes import sio_routes  # noqa: E402

# Wrap FastAPI app with Socket.IO, Socket.IO will handle /socket.io/* requests
# All other requests will be passed to FastAPI
app = socketio.ASGIApp(
    socketio_server=sio,
    other_asgi_app=fastapi_app,
    socketio_path="socket.io"
)


async def run_server():
    config_uvicorn = uvicorn.Config(
        app,
        host="0.0.0.0",
        log_level="warning",
        port=int(app_config.get("SERVER", "PORT")),
    )
    server = uvicorn.Server(config_uvicorn)
    logger.info(
        "[server] Starting Server on http://localhost:{}",
        app_config.get("SERVER", "PORT"),
    )
    await server.serve()
