import builtins
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock

from peewee import SqliteDatabase

src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Create a test in-memory SQLite database
test_db = SqliteDatabase(":memory:")

# Mock config before importing any db modules
mock_config = MagicMock()


def mock_get(section, option, fallback=None):
    if section == "DB":
        return {
            "VERBOSE_LOGGING": "false",
            "USER": "test_user",
            "PASSWORD": "",
            "HOST": "localhost",
        }.get(option, fallback or "")
    elif section == "TELEGRAM":
        return {
            "TG_ADMIN_USERS": "123456,789012",
            "YTDL_MAX_DOWNLOAD_TIME": "300",
            "BOT_USERNAME": "chaddi_bot",
        }.get(option, fallback or "")
    return fallback or ""


mock_config.get = mock_get

# Patch config module
sys.modules["src.domain.config"] = MagicMock(get_config=lambda: mock_config)

# Patch PostgresqlExtDatabase to use SQLite instead
mock_postgres = MagicMock()
mock_postgres.PostgresqlExtDatabase = lambda *args, **kwargs: test_db
mock_postgres.BinaryJSONField = MagicMock()
sys.modules["playhouse.postgres_ext"] = mock_postgres

# Mock spacy and related imports to avoid dependency issues
sys.modules["en_core_web_sm"] = MagicMock()
sys.modules["spacy"] = MagicMock()

# Mock remind handler to avoid circular import
sys.modules["src.bot.handlers.remind"] = MagicMock()
sys.modules["src.bot.handlers.remind"].build_job_name = lambda *args: "_".join(
    str(arg) for arg in args
)
sys.modules["src.bot.handlers.remind"].reminder_handler = lambda *args: None


# Mock FastAPI StaticFiles to avoid directory dependency
def mock_static_files(*args, **kwargs):
    mock = MagicMock()
    mock.directory = "/mock/static"
    return mock


sys.modules["starlette.staticfiles"] = MagicMock()
sys.modules["starlette.staticfiles"].StaticFiles = mock_static_files

# Mock builtins.open for util.py resource loading
original_open = open


def patched_open(file, *args, **kwargs):
    if "verb-past-lookup.json" in str(file) or "preposition-to-verb-map.json" in str(file):
        return StringIO("{}")
    return original_open(file, *args, **kwargs)


builtins.open = patched_open
