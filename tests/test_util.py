from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from telegram import Chat, Message, Update, User

from src.domain.util import (
    build_unsplash_image_url,
    choose_random_element_from_list,
    extract_pretty_name_from_tg_user,
    fetch_random_unsplash_photo_path,
    get_group_id_from_update,
    get_nlp,
    get_verb_past_lookup,
    normalize_datetime,
    pretty_print_rokda,
    pretty_time_delta,
)


def test_pretty_print_rokda_rounding():
    result = pretty_print_rokda(1234.567)
    assert result == "1,234.57"


def test_pretty_print_rokda_integer():
    result = pretty_print_rokda(1000)
    assert result == "1,000"


def test_pretty_print_rokda_small_value():
    result = pretty_print_rokda(1.234)
    assert result == "1.23"


def test_pretty_print_rokda_large_value():
    result = pretty_print_rokda(999999.999)
    assert result == "1,000,000.0"


def test_pretty_time_delta_seconds():
    result = pretty_time_delta(30)
    assert result == "30s"


def test_pretty_time_delta_minutes():
    result = pretty_time_delta(150)
    assert result == "2m 30s"


def test_pretty_time_delta_hours():
    result = pretty_time_delta(3665)
    assert result == "1h 1m 5s"


def test_pretty_time_delta_days():
    result = pretty_time_delta(90061)
    assert result == "1d 1h 1m 1s"


def test_pretty_time_delta_years():
    result = pretty_time_delta(31622461)
    assert result == "1y 1d 0h 1m 1s"


def test_pretty_time_delta_zero():
    result = pretty_time_delta(0)
    assert result == "0s"


def test_choose_random_element_from_list_single():
    result = choose_random_element_from_list(["only"])
    assert result == "only"


def test_choose_random_element_from_list_multiple():
    result = choose_random_element_from_list([1, 2, 3, 4, 5])
    assert result in [1, 2, 3, 4, 5]


def test_choose_random_element_from_list_empty():
    test_list = []
    import pytest

    with pytest.raises(IndexError):
        choose_random_element_from_list(test_list)


def test_extract_pretty_name_from_tg_user_username():
    user = MagicMock(spec=User)
    user.username = "testuser"
    user.first_name = None
    user.full_name = None
    user.id = 123

    result = extract_pretty_name_from_tg_user(user)
    assert result == "@testuser"


def test_extract_pretty_name_from_tg_user_first_name():
    user = MagicMock(spec=User)
    user.username = None
    user.first_name = "John"
    user.full_name = None
    user.id = 123

    result = extract_pretty_name_from_tg_user(user)
    assert result == "John"


def test_extract_pretty_name_from_tg_user_full_name():
    user = MagicMock(spec=User)
    user.username = None
    user.first_name = None
    user.full_name = "John Doe"
    user.id = 123

    result = extract_pretty_name_from_tg_user(user)
    assert result == "John Doe"


def test_extract_pretty_name_from_tg_user_id_only():
    user = MagicMock(spec=User)
    user.username = None
    user.first_name = None
    user.full_name = None
    user.id = 123

    result = extract_pretty_name_from_tg_user(user)
    assert result == "123"


def test_get_group_id_from_update_group():
    chat = MagicMock(spec=Chat)
    chat.id = -1001234567890
    chat.type = "group"

    message = MagicMock(spec=Message)
    message.chat = chat

    update = MagicMock(spec=Update)
    update.message = message

    result = get_group_id_from_update(update)
    assert result == -1001234567890


def test_get_group_id_from_update_supergroup():
    chat = MagicMock(spec=Chat)
    chat.id = -1001234567890
    chat.type = "supergroup"

    message = MagicMock(spec=Message)
    message.chat = chat

    update = MagicMock(spec=Update)
    update.message = message

    result = get_group_id_from_update(update)
    assert result == -1001234567890


def test_get_group_id_from_update_private_chat():
    chat = MagicMock(spec=Chat)
    chat.id = 123456789
    chat.type = "private"

    message = MagicMock(spec=Message)
    message.chat = chat

    update = MagicMock(spec=Update)
    update.message = message

    result = get_group_id_from_update(update)
    assert result is None


def test_get_group_id_from_update_no_message():
    update = MagicMock(spec=Update)
    update.message = None

    result = get_group_id_from_update(update)
    assert result is None


def test_normalize_datetime_naive():
    dt = datetime(2024, 1, 1, 12, 0, 0)

    result = normalize_datetime(dt)

    assert result.hour == 17
    assert result.minute == 30
    assert result.tzinfo is not None


def test_normalize_datetime_aware():
    import pytz

    dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)

    result = normalize_datetime(dt)

    assert result.hour == 17
    assert result.minute == 30
    assert result.tzinfo is not None


def test_normalize_datetime_stdlib_timezone():
    dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

    result = normalize_datetime(dt)

    assert result.hour == 17
    assert result.minute == 30
    assert result.tzinfo is not None


def test_get_verb_past_lookup():
    """Test get_verb_past_lookup function."""
    result = get_verb_past_lookup()
    assert isinstance(result, dict)


def test_get_nlp():
    """Test get_nlp function."""
    result = get_nlp()
    assert result is not None


def test_build_unsplash_image_url_with_existing_query():
    raw_url = "https://images.unsplash.com/photo-123?ixid=abc"

    result = build_unsplash_image_url(raw_url, 1280, 720)

    assert result == "https://images.unsplash.com/photo-123?ixid=abc&w=1280&h=720&fit=crop&fm=jpg"


def test_build_unsplash_image_url_without_query():
    raw_url = "https://images.unsplash.com/photo-123"

    result = build_unsplash_image_url(raw_url, 1280, 720)

    assert result == "https://images.unsplash.com/photo-123?w=1280&h=720&fit=crop&fm=jpg"


def test_fetch_random_unsplash_photo_path_missing_access_key():
    with patch("src.domain.util.UNSPLASH_ACCESS_KEY", None):
        result = fetch_random_unsplash_photo_path(1280, 720)

    assert result is None


@patch("src.domain.util.acquire_external_resource")
@patch("src.domain.util.requests.get")
def test_fetch_random_unsplash_photo_path_success(mock_get, mock_acquire):
    photo_response = MagicMock()
    photo_response.json.return_value = {
        "urls": {"raw": "https://images.unsplash.com/photo-123?ixid=abc"},
        "links": {"download_location": "https://api.unsplash.com/photos/123/download"},
    }
    photo_response.raise_for_status = MagicMock()

    download_response = MagicMock()
    download_response.raise_for_status = MagicMock()
    mock_get.side_effect = [photo_response, download_response]
    mock_acquire.return_value = "resources/external/test.jpg"

    with patch("src.domain.util.UNSPLASH_ACCESS_KEY", "test-access-key"):
        result = fetch_random_unsplash_photo_path(1280, 1280, query="nature,water,india")

    assert result == "resources/external/test.jpg"
    assert mock_get.call_count == 2

    random_photo_call = mock_get.call_args_list[0]
    assert random_photo_call.args[0] == "https://api.unsplash.com/photos/random"
    assert random_photo_call.kwargs["params"] == {
        "query": "nature,water,india",
        "orientation": "squarish",
    }
    assert random_photo_call.kwargs["headers"]["Authorization"] == "Client-ID test-access-key"

    mock_acquire.assert_called_once_with(
        "https://images.unsplash.com/photo-123?ixid=abc&w=1280&h=1280&fit=crop&fm=jpg",
        mock_acquire.call_args.args[1],
    )
