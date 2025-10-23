import subprocess
from datetime import datetime

from loguru import logger

from src.domain import util

CHADDI_TG_VERSION = "3.0.0"

GIT_COMMIT_ID = (
    subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).strip().decode("utf-8")
)

GIT_COMMIT_TIME = util.normalize_datetime(
    datetime.utcfromtimestamp(
        int(subprocess.check_output(["git", "show", "-s", "--format=%ct"]).strip().decode("utf-8"))
    )
)


GIT_COMMIT_MESSAGE = (
    subprocess.check_output(["git", "show", "-s", "--format=%B"]).strip().decode("utf-8")
)


TIME_SERVICE_STARTED = datetime.now()

logger.info(
    "[version] parsed GIT_COMMIT_ID={} GIT_COMMIT_TIME={} GIT_COMMIT_MESSAGE={} TIME_SERVICE_STARTED={}",
    GIT_COMMIT_ID,
    GIT_COMMIT_TIME,
    GIT_COMMIT_MESSAGE,
    TIME_SERVICE_STARTED,
)


def get_version():
    now = datetime.now()
    uptime = now - TIME_SERVICE_STARTED

    return {
        "semver": CHADDI_TG_VERSION,
        "git_commit_id": GIT_COMMIT_ID,
        "git_commit_time": GIT_COMMIT_TIME,
        "time_service_started": TIME_SERVICE_STARTED,
        "pretty_uptime": util.pretty_time_delta(uptime.seconds),
        "git_commit_message": GIT_COMMIT_MESSAGE,
    }
