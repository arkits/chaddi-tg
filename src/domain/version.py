import subprocess
from datetime import datetime

from loguru import logger

from src.domain import util


def _get_version_from_git():
    """
    Derive semantic version from git commit count.
    Starts from 3.0.0 and adds commit count to the patch version.

    Returns:
        str: Semantic version string (e.g., "3.0.5" for 5 commits)
    """
    base_version = "3.0.0"
    try:
        # Get total commit count
        commit_count = (
            subprocess.check_output(
                ["git", "rev-list", "--count", "HEAD"],
                stderr=subprocess.DEVNULL,
            )
            .strip()
            .decode("utf-8")
        )
        # Add commit count to patch version: 3.0.0 + commits = 3.0.COMMITS
        return f"3.0.{commit_count}"
    except subprocess.CalledProcessError:
        # Git command failed (not a git repo, git not available, etc.)
        logger.warning("[version] Failed to get commit count from git, using base version")
        return base_version
    except Exception as e:
        logger.warning("[version] Error getting commit count from git: {}, using base version", e)
        return base_version


CHADDI_TG_VERSION = _get_version_from_git()
logger.info("[version] Derived semantic version from git: {}", CHADDI_TG_VERSION)

GIT_COMMIT_ID = (
    subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).strip().decode("utf-8")
)

GIT_COMMIT_TIME = util.normalize_datetime(
    datetime.fromtimestamp(
        int(subprocess.check_output(["git", "show", "-s", "--format=%ct"]).strip().decode("utf-8")),
        tz=datetime.UTC,
    )
)


GIT_COMMIT_MESSAGE = (
    subprocess.check_output(["git", "show", "-s", "--format=%B"]).strip().decode("utf-8")
)


TIME_SERVICE_STARTED = util.normalize_datetime(datetime.now(datetime.UTC))

logger.info(
    "[version] parsed GIT_COMMIT_ID={} GIT_COMMIT_TIME={} GIT_COMMIT_MESSAGE={} TIME_SERVICE_STARTED={}",
    GIT_COMMIT_ID,
    GIT_COMMIT_TIME,
    GIT_COMMIT_MESSAGE,
    TIME_SERVICE_STARTED,
)


def get_version():
    now = util.normalize_datetime(datetime.now(datetime.UTC))
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
