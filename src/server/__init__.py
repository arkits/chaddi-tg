import asyncio
from pathlib import Path

import sentry_sdk
import socketio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from loguru import logger
from starlette.exceptions import HTTPException
from starlette_exporter import PrometheusMiddleware, handle_metrics

from src.domain import config, version
from src.server.routes import api_routes

app_config = config.get_config()
FRONTEND_DIST_DIR = Path(__file__).resolve().parents[2] / "frontend" / "dist"
RESERVED_FRONTEND_PREFIXES = {"api", "metrics", "socket.io"}


tags_metadata = [
    {
        "name": "api",
        "description": "Chaddi API Endpoints",
    },
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

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
)

fastapi_app.sio = sio

fastapi_app.include_router(api_routes.router, prefix="/api", tags=["api"])

from src.server.routes import sio_routes  # noqa: E402


def get_frontend_response(frontend_path: str = ""):
    """Serve Vite build assets and fall back to index.html for SPA routes."""
    top_level_path = frontend_path.split("/", maxsplit=1)[0]
    if top_level_path in RESERVED_FRONTEND_PREFIXES:
        raise HTTPException(status_code=404)

    dist_dir = FRONTEND_DIST_DIR.resolve()
    index_path = dist_dir / "index.html"

    if frontend_path:
        requested_path = (dist_dir / frontend_path).resolve()
        try:
            requested_path.relative_to(dist_dir)
        except ValueError as exc:
            raise HTTPException(status_code=404) from exc

        if requested_path.is_file():
            return FileResponse(requested_path)

    if index_path.is_file():
        return FileResponse(index_path)

    raise HTTPException(
        status_code=404,
        detail="Frontend build not found. Run `cd frontend && bun run build`.",
    )


@fastapi_app.get("/", include_in_schema=False)
@fastapi_app.get("/{frontend_path:path}", include_in_schema=False)
async def serve_frontend(frontend_path: str = ""):
    return get_frontend_response(frontend_path)


app = socketio.ASGIApp(socketio_server=sio, other_asgi_app=fastapi_app, socketio_path="socket.io")


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
