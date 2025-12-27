from datetime import datetime
from unittest.mock import MagicMock

from telegram import Chat, Message, Update, User

from src.domain.util import (
    choose_random_element_from_list,
    extract_pretty_name_from_tg_user,
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
    assert result == "30ds"


def test_pretty_time_delta_minutes():
    result = pretty_time_delta(150)
    assert result == "2dm 30ds"


def test_pretty_time_delta_hours():
    result = pretty_time_delta(3665)
    assert result == "1dh 1dm 5ds"


def test_pretty_time_delta_days():
    result = pretty_time_delta(90061)
    assert result == "1dd 1dh 1dm 1ds"


def test_pretty_time_delta_years():
    result = pretty_time_delta(31622461)
    assert result == "1dy 1dd 0dh 1dm 1ds"


def test_pretty_time_delta_zero():
    result = pretty_time_delta(0)
    assert result == "0ds"


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


def test_get_verb_past_lookup():
    """Test get_verb_past_lookup function."""
    result = get_verb_past_lookup()
    assert isinstance(result, dict)


def test_get_nlp():
    """Test get_nlp function."""
    result = get_nlp()
    assert result is not None
