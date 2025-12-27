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


TIME_SERVICE_STARTED = util.normalize_datetime(datetime.utcnow())

logger.info(
    "[version] parsed GIT_COMMIT_ID={} GIT_COMMIT_TIME={} GIT_COMMIT_MESSAGE={} TIME_SERVICE_STARTED={}",
    GIT_COMMIT_ID,
    GIT_COMMIT_TIME,
    GIT_COMMIT_MESSAGE,
    TIME_SERVICE_STARTED,
)


def get_version():
    now = util.normalize_datetime(datetime.utcnow())
    uptime = now - TIME_SERVICE_STARTED

    # Format times consistently (remove microseconds)
    def format_datetime(dt):
        dt_no_micro = dt.replace(microsecond=0)
        # Use isoformat and replace 'T' with space to get YYYY-MM-DD HH:MM:SS+05:30 format
        return dt_no_micro.isoformat().replace("T", " ")

    git_commit_time_str = format_datetime(GIT_COMMIT_TIME)
    time_started_str = format_datetime(TIME_SERVICE_STARTED)

    return {
        "semver": CHADDI_TG_VERSION,
        "git_commit_id": GIT_COMMIT_ID,
        "git_commit_time": git_commit_time_str,
        "time_service_started": time_started_str,
        "pretty_uptime": util.pretty_time_delta(uptime.seconds),
        "git_commit_message": GIT_COMMIT_MESSAGE,
    }
