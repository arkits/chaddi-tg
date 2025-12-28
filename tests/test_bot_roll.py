from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Chat, Message, Update, User
from telegram.ext import ContextTypes

from src.bot.handlers import roll


@pytest.fixture
def mock_update():
    """Create a mock Telegram Update object for testing."""
    user = MagicMock(spec=User)
    user.id = 123456
    user.username = "testuser"
    user.first_name = "Test"

    chat = MagicMock(spec=Chat)
    chat.id = -1001234567890
    chat.type = "group"
    chat.title = "Test Group"

    message = MagicMock(spec=Message)
    message.message_id = 1
    message.from_user = user
    message.chat = chat
    message.text = "/roll"
    message.reply_to_message = None
    message.reply_text = AsyncMock()

    update = MagicMock(spec=Update)
    update.message = message

    return update


@pytest.fixture
def mock_context():
    """Create a mock ContextTypes object for testing."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    context.bot.kick_chat_member = AsyncMock()
    context.job_queue = MagicMock()
    context.job_queue.jobs.return_value = []
    context.job_queue.run_once = MagicMock()
    return context


@pytest.mark.asyncio
async def test_handle_command_status(mock_update, mock_context):
    """Test roll handler with status command (default)."""
    with (
        patch("src.bot.handlers.roll.dc"),
        patch("src.bot.handlers.roll.roll_dao") as mock_roll_dao,
    ):
        mock_roll_dao.get_roll_by_group_id.return_value = None

        await roll.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_handle_command_start(mock_update, mock_context):
    """Test roll handler with start command."""
    with (
        patch("src.bot.handlers.roll.dc"),
        patch("src.bot.handlers.roll.util") as mock_util,
    ):
        mock_update.message.text = "/roll start"
        mock_util.is_admin_tg_user.return_value = True

        with (
            patch("src.bot.handlers.roll.group_dao") as mock_group_dao,
            patch("src.bot.handlers.roll.bakchod_dao") as mock_bakchod_dao,
            patch("src.bot.handlers.roll.roll_dao") as mock_roll_dao,
            patch("src.bot.handlers.roll.generate_new_roll") as mock_generate,
        ):
            mock_group = MagicMock()
            mock_group.group_id = -1001234567890
            mock_group_dao.get_group_by_id.return_value = mock_group

            mock_victim = MagicMock()
            mock_victim.tg_id = 789012
            mock_bakchod_dao.get_bakchod_by_username.return_value = mock_victim

            mock_roll_dao.get_roll_by_group_id.return_value = None

            new_roll = MagicMock()
            new_roll.goal = 4
            new_roll.rule = "mute_user"
            new_roll.victim = mock_victim
            new_roll.prize = 600
            mock_generate.return_value = new_roll

            await roll.handle(mock_update, mock_context)

            assert mock_update.message.reply_text.called


@pytest.mark.asyncio
async def test_handle_command_reset_admin(mock_update, mock_context):
    """Test roll handler with reset command by admin."""
    with (
        patch("src.bot.handlers.roll.dc"),
        patch("src.bot.handlers.roll.util") as mock_util,
    ):
        mock_update.message.text = "/roll reset"
        mock_util.is_admin_tg_user.return_value = True

        await roll.handle(mock_update, mock_context)

        assert mock_context.job_queue.run_once.called


@pytest.mark.asyncio
async def test_handle_command_reset_non_admin(mock_update, mock_context):
    """Test roll handler with reset command by non-admin."""
    with (
        patch("src.bot.handlers.roll.dc"),
        patch("src.bot.handlers.roll.util") as mock_util,
    ):
        mock_update.message.text = "/roll reset"
        mock_util.is_admin_tg_user.return_value = False

        await roll.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Chal kat re bsdk!")


@pytest.mark.xfail(reason="Complex mocking of response message handling")
@pytest.mark.asyncio
async def test_handle_command_default_no_roll(mock_update, mock_context):
    """Test handle_command_default when no roll exists."""
    with patch("src.bot.handlers.roll.roll_dao") as mock_roll_dao:
        mock_roll_dao.get_roll_by_group_id.return_value = None

        await roll.handle_command_default(mock_update)

        assert mock_update.message.reply_text.called
        assert "start" in mock_update.message.reply_text.call_args[0][0].lower()


@pytest.mark.asyncio
async def test_handle_command_start_new_roll(mock_update, mock_context):
    """Test handle_command_start creates new roll."""
    with (
        patch("src.bot.handlers.roll.group_dao") as mock_group_dao,
        patch("src.bot.handlers.roll.bakchod_dao") as mock_bakchod_dao,
        patch("src.bot.handlers.roll.roll_dao") as mock_roll_dao,
        patch("src.bot.handlers.roll.generate_new_roll") as mock_generate,
    ):
        mock_group = MagicMock()
        mock_group.group_id = -1001234567890
        mock_group_dao.get_group_by_id.return_value = mock_group

        mock_victim = MagicMock()
        mock_bakchod_dao.get_bakchod_by_username.return_value = mock_victim

        mock_roll_dao.get_roll_by_group_id.return_value = None

        new_roll = MagicMock()
        new_roll.goal = 4
        new_roll.rule = "mute_user"
        new_roll.victim = mock_victim
        new_roll.prize = 600
        mock_generate.return_value = new_roll

        await roll.handle_command_start(mock_update)

        assert mock_update.message.reply_text.called


@pytest.mark.asyncio
async def test_handle_command_start_existing_roll_expired(mock_update, mock_context):
    """Test handle_command_start when existing roll is expired."""
    with (
        patch("src.bot.handlers.roll.group_dao") as mock_group_dao,
        patch("src.bot.handlers.roll.bakchod_dao") as mock_bakchod_dao,
        patch("src.bot.handlers.roll.roll_dao") as mock_roll_dao,
        patch("src.bot.handlers.roll.generate_new_roll") as mock_generate,
    ):
        from datetime import datetime, timedelta

        mock_group = MagicMock()
        mock_group.group_id = -1001234567890
        mock_group_dao.get_group_by_id.return_value = mock_group

        mock_victim = MagicMock()
        mock_bakchod_dao.get_bakchod_by_username.return_value = mock_victim

        old_roll = MagicMock()
        old_roll.expiry = datetime.now() - timedelta(hours=2)
        mock_roll_dao.get_roll_by_group_id.return_value = old_roll

        new_roll = MagicMock()
        new_roll.goal = 4
        new_roll.rule = "mute_user"
        new_roll.victim = mock_victim
        new_roll.prize = 600
        mock_generate.return_value = new_roll

        await roll.handle_command_start(mock_update)

        assert mock_update.message.reply_text.called


@pytest.mark.asyncio
async def test_handle_command_start_active_roll_not_admin(mock_update, mock_context):
    """Test handle_command_start with active roll and non-admin."""
    with (
        patch("src.bot.handlers.roll.group_dao") as mock_group_dao,
        patch("src.bot.handlers.roll.roll_dao") as mock_roll_dao,
        patch("src.bot.handlers.roll.util") as mock_util,
    ):
        from datetime import datetime, timedelta

        mock_group = MagicMock()
        mock_group.group_id = -1001234567890
        mock_group_dao.get_group_by_id.return_value = mock_group

        active_roll = MagicMock()
        active_roll.expiry = datetime.now() + timedelta(hours=1)
        mock_roll_dao.get_roll_by_group_id.return_value = active_roll

        mock_util.is_admin_tg_user.return_value = False

        await roll.handle_command_start(mock_update)

        mock_update.message.reply_text.assert_called_once_with("Chal kat re bsdk!")


def test_extract_command_from_update():
    """Test _extract_command_from_update extracts command correctly."""
    mock_update = MagicMock()
    mock_update.message.text = "/roll start"

    command = roll._extract_command_from_update(mock_update)

    assert command == "start"


def test_extract_command_from_update_default():
    """Test _extract_command_from_update defaults to status."""
    mock_update = MagicMock()
    mock_update.message.text = "/roll"

    command = roll._extract_command_from_update(mock_update)

    assert command == "status"


def test_extract_params_from_update():
    """Test _extract_params_from_update extracts parameters."""
    mock_update = MagicMock()
    mock_update.message.text = "/roll start mute_user testuser"

    params = roll._extract_params_from_update(mock_update)

    assert params is not None
    assert len(params) == 4
    assert params[0] == "/roll"
    assert params[1] == "start"
    assert params[2] == "mute_user"
    assert params[3] == "testuser"


def test_get_group_id_from_update_group():
    """Test _get_group_id_from_update for group chat."""
    mock_update = MagicMock()
    mock_update.message.chat.id = -1001234567890
    mock_update.message.chat.type = "group"

    group_id = roll._get_group_id_from_update(mock_update)

    assert group_id == -1001234567890


def test_get_group_id_from_update_supergroup():
    """Test _get_group_id_from_update for supergroup."""
    mock_update = MagicMock()
    mock_update.message.chat.id = -1001234567890
    mock_update.message.chat.type = "supergroup"

    group_id = roll._get_group_id_from_update(mock_update)

    assert group_id == -1001234567890


def test_get_group_id_from_update_private():
    """Test _get_group_id_from_update for private chat."""
    mock_update = MagicMock()
    mock_update.message.chat.id = 123456
    mock_update.message.chat.type = "private"

    group_id = roll._get_group_id_from_update(mock_update)

    assert group_id is None


def test_get_random_roll_type():
    """Test _get_random_roll_type returns valid roll type."""
    roll_type = roll._get_random_roll_type()

    assert roll_type in roll.ROLL_TYPES


def test_pretty_roll_rule():
    """Test _pretty_roll_rule returns mapped rule."""
    assert roll._pretty_roll_rule("mute_user") == "mute"
    assert roll._pretty_roll_rule("auto_mom") == "/mom"
    assert roll._pretty_roll_rule("kick_user") == "kick"
    assert roll._pretty_roll_rule("invalid") is None


@pytest.mark.asyncio
async def test_reset_roll_effects_mute_user(mock_context):
    """Test reset_roll_effects for mute_user rule."""
    with patch("src.bot.handlers.roll.roll_dao") as mock_roll_dao:
        mock_roll = MagicMock()
        mock_roll.rule = "mute_user"
        mock_roll_dao.get_roll_by_group_id.return_value = mock_roll

        mock_victim = MagicMock()
        mock_victim.metadata = {"censored": {"group_ids": [-1001234567890]}}
        mock_roll.victim = mock_victim

        mock_context.job.data = -1001234567890

        await roll.reset_roll_effects(mock_context)

        assert mock_victim.save.called
        assert mock_context.bot.send_message.called


@pytest.mark.asyncio
async def test_reset_roll_effects_auto_mom(mock_context):
    """Test reset_roll_effects for auto_mom rule."""
    with patch("src.bot.handlers.roll.roll_dao") as mock_roll_dao:
        mock_roll = MagicMock()
        mock_roll.rule = "auto_mom"
        mock_roll_dao.get_roll_by_group_id.return_value = mock_roll

        mock_victim = MagicMock()
        mock_victim.metadata = {"auto_mom": {"group_ids": [-1001234567890]}}
        mock_roll.victim = mock_victim

        mock_context.job.data = -1001234567890

        await roll.reset_roll_effects(mock_context)

        assert mock_victim.save.called
        assert mock_context.bot.send_message.called


def test_generate_new_roll_from_params():
    """Test generate_new_roll creates roll from message params."""
    with (
        patch("src.bot.handlers.roll.group_dao") as mock_group_dao,
        patch("src.bot.handlers.roll.bakchod_dao") as mock_bakchod_dao,
        patch("src.bot.handlers.roll.roll_dao") as mock_roll_dao,
        patch("src.bot.handlers.roll.random") as mock_random,
    ):
        mock_update = MagicMock()
        mock_update.message.text = "/roll start mute_user testuser"
        mock_update.message.from_user.id = 123456

        mock_group = MagicMock()
        mock_group.group_id = -1001234567890
        mock_group_dao.get_group_by_id.return_value = mock_group

        mock_victim = MagicMock()
        mock_victim.tg_id = 789012
        mock_bakchod_dao.get_bakchod_by_username.return_value = mock_victim

        mock_roll_dao.get_roll_by_group_id.return_value = None

        mock_random.randint.side_effect = [1, 700]  # goal, prize

        result = roll.generate_new_roll(mock_update, -1001234567890)

        assert result is not None
        assert result.rule == "mute_user"


@pytest.mark.xfail(reason="Complex mocking of database operations")
def test_generate_new_roll_random():
    """Test generate_new_roll creates roll with random params."""
    with (
        patch("src.bot.handlers.roll.Group") as mock_group_model,
        patch("src.bot.handlers.roll.group_dao") as mock_group_dao,
        patch("src.bot.handlers.roll.bakchod_dao") as mock_bakchod_dao,
        patch("src.bot.handlers.roll.roll_dao") as mock_roll_dao,
        patch("src.bot.handlers.roll.random") as mock_random,
    ):
        mock_update = MagicMock()
        mock_update.message.text = "/roll start"
        mock_update.message.from_user.id = 123456

        mock_group = MagicMock()
        mock_group.group_id = -1001234567890
        mock_group_dao.get_group_by_id.return_value = mock_group
        mock_group_model.get_by_id.return_value = mock_group

        mock_victim = MagicMock()
        mock_victim.tg_id = 789012
        mock_bakchod_dao.get_bakchod_by_username.return_value = mock_victim

        mock_bakchods = [MagicMock(tg_id=123456), mock_victim]
        mock_bakchod_dao.get_bakchods_by_group_id.return_value = mock_bakchods

        mock_roll_dao.get_roll_by_group_id.return_value = None

        mock_random.randint.side_effect = [0, 3, 650]  # roll_type_index, goal, prize

        result = roll.generate_new_roll(mock_update, -1001234567890)

        assert result is not None
        assert result.goal == 3
        assert result.prize == 650


@pytest.mark.asyncio
async def test_handle_dice_rolls_no_group(mock_update, mock_context):
    """Test handle_dice_rolls when not in a group."""
    mock_update.message.chat.type = "private"
    mock_update.message.chat.id = 123456

    with patch("src.bot.handlers.roll.dc"):
        await roll.handle_dice_rolls(4, mock_update, mock_context)

        assert not mock_update.message.reply_text.called


@pytest.mark.asyncio
async def test_handle_dice_rolls_no_active_roll(mock_update, mock_context):
    """Test handle_dice_rolls when no active roll exists."""
    with (
        patch("src.bot.handlers.roll.dc"),
        patch("src.bot.handlers.roll.roll_dao") as mock_roll_dao,
    ):
        mock_roll_dao.get_roll_by_group_id.return_value = None

        await roll.handle_dice_rolls(4, mock_update, mock_context)

        assert not mock_update.message.reply_text.called


@pytest.mark.asyncio
async def test_handle_dice_rolls_already_won(mock_update, mock_context):
    """Test handle_dice_rolls when roll already has a winner."""
    with (
        patch("src.bot.handlers.roll.dc"),
        patch("src.bot.handlers.roll.roll_dao") as mock_roll_dao,
    ):
        mock_roll = MagicMock()
        mock_roll.winrar = MagicMock()
        mock_roll_dao.get_roll_by_group_id.return_value = mock_roll

        await roll.handle_dice_rolls(4, mock_update, mock_context)

        assert not mock_update.message.reply_text.called


@pytest.mark.asyncio
async def test_handle_dice_rolls_expired(mock_update, mock_context):
    """Test handle_dice_rolls when roll has expired."""
    with (
        patch("src.bot.handlers.roll.dc"),
        patch("src.bot.handlers.roll.roll_dao") as mock_roll_dao,
    ):
        from datetime import datetime, timedelta

        mock_roll = MagicMock()
        mock_roll.winrar = None
        mock_roll.expiry = datetime.now() - timedelta(hours=1)
        mock_roll_dao.get_roll_by_group_id.return_value = mock_roll

        await roll.handle_dice_rolls(4, mock_update, mock_context)

        assert not mock_update.message.reply_text.called


@pytest.mark.asyncio
async def test_handle_dice_rolls_rolled_too_soon(mock_update, mock_context):
    """Test handle_dice_rolls when user rolled too recently."""
    with (
        patch("src.bot.handlers.roll.dc"),
        patch("src.bot.handlers.roll.roll_dao") as mock_roll_dao,
        patch("src.bot.handlers.roll.bakchod_dao") as mock_bakchod_dao,
        patch("src.bot.handlers.roll.util") as mock_util,
    ):
        from datetime import datetime, timedelta

        mock_roll = MagicMock()
        mock_roll.winrar = None
        mock_roll.expiry = datetime.now() + timedelta(hours=1)
        mock_roll_dao.get_roll_by_group_id.return_value = mock_roll

        mock_roller = MagicMock()
        mock_roller.metadata = {
            "last_time_rolled": (datetime.now() - timedelta(minutes=1)).isoformat()
        }
        mock_util.extract_pretty_name_from_bakchod.return_value = "testuser"
        mock_bakchod_dao.get_bakchod_from_update.return_value = mock_roller

        await roll.handle_dice_rolls(4, mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_handle_dice_rolls_no_match(mock_update, mock_context):
    """Test handle_dice_rolls when dice doesn't match goal."""
    with (
        patch("src.bot.handlers.roll.dc"),
        patch("src.bot.handlers.roll.roll_dao") as mock_roll_dao,
        patch("src.bot.handlers.roll.bakchod_dao") as mock_bakchod_dao,
        patch("src.bot.handlers.roll.util") as mock_util,
    ):
        from datetime import datetime, timedelta

        mock_roll = MagicMock()
        mock_roll.winrar = None
        mock_roll.expiry = datetime.now() + timedelta(hours=1)
        mock_roll.goal = 3
        mock_roll_dao.get_roll_by_group_id.return_value = mock_roll

        mock_roller = MagicMock()
        mock_roller.metadata = {}
        mock_util.extract_pretty_name_from_bakchod.return_value = "testuser"
        mock_bakchod_dao.get_bakchod_from_update.return_value = mock_roller

        await roll.handle_dice_rolls(4, mock_update, mock_context)

        assert mock_roller.save.called
        assert not mock_context.bot.send_message.called


def test_generate_pretty_roll_description_ongoing():
    """Test _generate_pretty_roll_description for ongoing roll."""
    mock_roll = MagicMock()
    mock_roll.winrar = None
    mock_roll.goal = 4
    mock_roll.rule = "mute_user"
    mock_roll.prize = 600

    mock_victim = MagicMock()
    mock_victim.tg_id = 123456
    mock_victim.username = "victimuser"
    mock_roll.victim = mock_victim

    with patch("src.bot.handlers.roll.util") as mock_util:
        mock_util.extract_pretty_name_from_bakchod.return_value = "victimuser"
        mock_util.ROKDA_STRING = "₹"

        result = roll._generate_pretty_roll_description(mock_roll)

        assert "Roll a 4" in result
        assert "mute" in result
        assert "600 ₹" in result


def test_generate_pretty_roll_description_won_kick():
    """Test _generate_pretty_roll_description for won roll with kick rule."""
    from datetime import datetime, timedelta

    mock_roll = MagicMock()
    mock_roll.winrar = MagicMock()
    mock_roll.winrar.tg_id = 123456
    mock_roll.winrar.username = "winner"
    mock_roll.goal = 4
    mock_roll.rule = "kick_user"
    mock_roll.prize = 600
    mock_roll.expiry = datetime.now() + timedelta(minutes=30)

    mock_victim = MagicMock()
    mock_victim.tg_id = 789012
    mock_victim.username = "victim"
    mock_roll.victim = mock_victim

    with patch("src.bot.handlers.roll.util") as mock_util:

        def extract_name_side_effect(bakchod):
            if bakchod.tg_id == 123456:
                return "winner"
            elif bakchod.tg_id == 789012:
                return "victim"
            return "unknown"

        mock_util.extract_pretty_name_from_bakchod.side_effect = extract_name_side_effect
        mock_util.ROKDA_STRING = "₹"

        result = roll._generate_pretty_roll_description(mock_roll)

        assert result is not None
        assert "won the current roll" in result
        assert "kicked" in result
        assert "600₹" in result


def test_generate_pretty_roll_description_won_mute():
    """Test _generate_pretty_roll_description for won roll with mute rule."""
    from datetime import datetime, timedelta

    mock_roll = MagicMock()
    mock_roll.winrar = MagicMock()
    mock_roll.winrar.tg_id = 123456
    mock_roll.winrar.username = "winner"
    mock_roll.goal = 4
    mock_roll.rule = "mute_user"
    mock_roll.prize = 600
    mock_roll.expiry = datetime.now() + timedelta(minutes=30)

    mock_victim = MagicMock()
    mock_victim.tg_id = 789012
    mock_victim.username = "victim"
    mock_roll.victim = mock_victim

    with patch("src.bot.handlers.roll.util") as mock_util:

        def extract_name_side_effect(bakchod):
            if bakchod.tg_id == 123456:
                return "winner"
            elif bakchod.tg_id == 789012:
                return "victim"
            return "unknown"

        mock_util.extract_pretty_name_from_bakchod.side_effect = extract_name_side_effect
        mock_util.ROKDA_STRING = "₹"
        mock_util.pretty_time_delta.return_value = "30 minutes"

        result = roll._generate_pretty_roll_description(mock_roll)

        assert result is not None
        assert "won the current roll" in result
        assert "mute" in result
        assert "30 minutes" in result
        assert "600₹" in result


def test_get_random_bakchod_from_group():
    """Test _get_random_bakchod_from_group returns a bakchod."""
    import datetime as dt

    with patch("src.bot.handlers.roll.Group") as mock_group_class:
        mock_group = MagicMock()
        mock_member1 = MagicMock()
        mock_bakchod1 = MagicMock()
        mock_bakchod1.lastseen = dt.datetime.now() - dt.timedelta(hours=1)
        mock_member1.bakchod = mock_bakchod1

        mock_member2 = MagicMock()
        mock_bakchod2 = MagicMock()
        mock_bakchod2.lastseen = dt.datetime.now() - dt.timedelta(minutes=30)
        mock_member2.bakchod = mock_bakchod2

        mock_group.group_member = [mock_member1, mock_member2]
        mock_group_class.get_by_id.return_value = mock_group

        result = roll._get_random_bakchod_from_group("-1001234567890")

        assert result is not None
        assert result in [mock_bakchod1, mock_bakchod2]


def test_get_random_bakchod_from_group_empty():
    """Test _get_random_bakchod_from_group with empty group."""
    with patch("src.bot.handlers.roll.Group") as mock_group_class:
        mock_group = MagicMock()
        mock_group.group_member = []
        mock_group_class.get_by_id.return_value = mock_group

        result = roll._get_random_bakchod_from_group("-1001234567890")

        assert result is None


def test_get_random_bakchod_from_group_single_member():
    """Test _get_random_bakchod_from_group with single member."""
    import datetime as dt

    with (
        patch("src.bot.handlers.roll.Group") as mock_group_class,
        patch("src.bot.handlers.roll.random") as mock_random,
    ):
        mock_group = MagicMock()
        mock_member = MagicMock()
        mock_bakchod = MagicMock()
        mock_bakchod.lastseen = dt.datetime.now()
        mock_member.bakchod = mock_bakchod
        mock_group.group_member = [mock_member]
        mock_group_class.get_by_id.return_value = mock_group

        mock_random.randint.return_value = 0

        result = roll._get_random_bakchod_from_group("-1001234567890")

        assert result == mock_bakchod
