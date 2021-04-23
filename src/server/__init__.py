import uvicorn
from loguru import logger
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette_exporter import PrometheusMiddleware, handle_metrics

from src.domain import config
from . import routes

# Initialize the config
app_config = config.get_config()

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    PrometheusMiddleware,
    app_name="chaddi-tg",
    prefix="http",
    buckets=[0.1, 0.25, 0.5, 0.75, 1],
)
app.add_route("/chaddi/metrics", handle_metrics)

app.include_router(routes.router, prefix="/chaddi")


def run_server():

    logger.info(
        "[server] Starting Server on http://localhost:{}/chaddi",
        app_config.get("SERVER", "PORT"),
    )
    uvicorn.run(
        app,
        host="0.0.0.0",
        log_level="warning",
        port=int(app_config.get("SERVER", "PORT")),
    )
