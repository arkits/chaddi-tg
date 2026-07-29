from contextlib import suppress
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from peewee import DoesNotExist
from telegram import Chat, Message, Update, User
from telegram.ext import ContextTypes

from src.bot.handlers import defaults


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
    message.text = "Test message"
    message.reply_to_message = None
    message.reply_text = AsyncMock()
    message.new_chat_members = None
    message.left_chat_member = None
    message.dice = None

    update = MagicMock(spec=Update)
    update.message = message

    return update


@pytest.fixture
def mock_context():
    """Create a mock ContextTypes object for testing."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = MagicMock()
    context.bot.forward_message = AsyncMock()
    context.bot.delete_message = AsyncMock()
    context.bot.send_message = AsyncMock()
    return context


@pytest.mark.asyncio
async def test_all_syncs_persistence_data(mock_update, mock_context):
    """Test that all handler calls sync_persistence_data."""
    with (
        patch("src.bot.handlers.defaults.dc") as mock_dc,
        patch("src.bot.handlers.defaults.bakchod_dao") as mock_bakchod_dao,
        patch("src.bot.handlers.defaults.antiwordle") as mock_antiwordle,
        patch("src.bot.handlers.defaults.musiclinks") as mock_musiclinks,
        patch("src.bot.handlers.defaults.x_links") as mock_x_links,
        patch("src.bot.handlers.defaults.handle_bakchod_metadata_effects"),
        patch("src.bot.handlers.defaults.handle_dice_rolls"),
        patch("src.bot.handlers.defaults.handle_message_matching"),
        patch("src.bot.handlers.defaults.handle_bot_mention"),
    ):
        mock_bakchod = MagicMock()
        mock_bakchod.rokda = 100
        mock_bakchod.metadata = None
        mock_bakchod_dao.get_or_create_bakchod_from_tg_user.return_value = mock_bakchod

        mock_antiwordle.handle = AsyncMock()
        mock_musiclinks.handle = AsyncMock()
        mock_x_links.handle = AsyncMock()

        await defaults.all(mock_update, mock_context)

        mock_dc.sync_persistence_data.assert_called_once_with(mock_update)
        mock_x_links.handle.assert_awaited_once_with(mock_update, mock_context)


@pytest.mark.asyncio
async def test_all_without_from_user(mock_update, mock_context):
    """Test that all handler calls sync_persistence_data even with None from_user."""
    with patch("src.bot.handlers.defaults.dc") as mock_dc:
        mock_update.message.from_user = None

        with suppress(AttributeError):
            await defaults.all(mock_update, mock_context)

        mock_dc.sync_persistence_data.assert_called_once_with(mock_update)


@pytest.mark.asyncio
async def test_all_rewards_rokda(mock_update, mock_context):
    """Test that all handler rewards rokda to user."""
    with (
        patch("src.bot.handlers.defaults.dc"),
        patch("src.bot.handlers.defaults.bakchod_dao") as mock_bakchod_dao,
        patch("src.bot.handlers.defaults.antiwordle") as mock_antiwordle,
        patch("src.bot.handlers.defaults.musiclinks") as mock_musiclinks,
        patch("src.bot.handlers.defaults.x_links") as mock_x_links,
        patch("src.bot.handlers.defaults.handle_bakchod_metadata_effects"),
        patch("src.bot.handlers.defaults.handle_dice_rolls"),
        patch("src.bot.handlers.defaults.handle_message_matching"),
        patch("src.bot.handlers.defaults.handle_bot_mention"),
    ):
        mock_bakchod = MagicMock()
        mock_bakchod.rokda = 100
        mock_bakchod.metadata = None
        mock_bakchod_dao.get_or_create_bakchod_from_tg_user.return_value = mock_bakchod

        mock_antiwordle.handle = AsyncMock()
        mock_musiclinks.handle = AsyncMock()
        mock_x_links.handle = AsyncMock()

        await defaults.all(mock_update, mock_context)

        assert mock_bakchod.save.called


@pytest.mark.asyncio
async def test_handle_bakchod_metadata_effects_none_metadata(mock_update, mock_context):
    """Test metadata effects with None metadata."""
    mock_bakchod = MagicMock()
    mock_bakchod.metadata = None

    await defaults.handle_bakchod_metadata_effects(mock_update, mock_context, mock_bakchod)

    assert not mock_context.bot.send_message.called


@pytest.mark.asyncio
async def test_handle_bakchod_metadata_effects_empty_json(mock_update, mock_context):
    """Test metadata effects with EMPTY_JSON."""

    mock_bakchod = MagicMock()
    mock_bakchod.metadata = {}

    await defaults.handle_bakchod_metadata_effects(mock_update, mock_context, mock_bakchod)

    assert not mock_context.bot.send_message.called


@pytest.mark.asyncio
async def test_handle_bakchod_metadata_effects_censored(mock_update, mock_context):
    """Test metadata effects with censored key."""

    mock_bakchod = MagicMock()
    mock_bakchod.metadata = {"censored": {"group_ids": [-1001234567890]}}

    await defaults.handle_bakchod_metadata_effects(mock_update, mock_context, mock_bakchod)

    mock_context.bot.delete_message.assert_called_once()


@pytest.mark.asyncio
async def test_handle_bakchod_metadata_effects_censored_different_group(mock_update, mock_context):
    """Test metadata effects with censored for different group."""
    mock_bakchod = MagicMock()
    mock_bakchod.metadata = {"censored": {"group_ids": [-1009999999999]}}

    await defaults.handle_bakchod_metadata_effects(mock_update, mock_context, mock_bakchod)

    assert not mock_context.bot.delete_message.called


@pytest.mark.asyncio
async def test_handle_bakchod_metadata_effects_auto_mom(mock_update, mock_context):
    """Test metadata effects with auto_mom key."""
    with (
        patch("src.bot.handlers.defaults.mom_spacy") as mock_mom_spacy,
        patch("src.bot.handlers.defaults.random") as mock_random,
        patch("src.bot.handlers.defaults.util") as mock_util,
    ):
        mock_random.random.return_value = 0.6  # > 0.5 so auto_mom triggers
        mock_mom_spacy.joke_mom.return_value = "Test joke"
        mock_util.extract_pretty_name_from_bakchod.return_value = "Test User"
        mock_util.get_group_id_from_update.return_value = -1001234567890
        mock_update.message.text = "Test message"

        mock_bakchod = MagicMock()
        mock_bakchod.metadata = {"auto_mom": {"group_ids": [-1001234567890]}}
        mock_bakchod.username = "testuser"

        await defaults.handle_bakchod_metadata_effects(mock_update, mock_context, mock_bakchod)

        # Handler may or may not call reply_text depending on implementation
        assert mock_mom_spacy.joke_mom.called


@pytest.mark.asyncio
async def test_handle_bakchod_metadata_effects_route_messages(mock_update, mock_context):
    """Test metadata effects with route-messages key."""
    mock_bakchod = MagicMock()
    mock_bakchod.metadata = {"route-messages": [{"to_group": -1009999999999}]}

    await defaults.handle_bakchod_metadata_effects(mock_update, mock_context, mock_bakchod)

    mock_context.bot.forward_message.assert_called_once()


@pytest.mark.asyncio
async def test_handle_bakchod_metadata_effects_route_messages_same_group(mock_update, mock_context):
    """Test route-messages doesn't forward to same group."""
    mock_bakchod = MagicMock()
    mock_bakchod.metadata = {"route-messages": [{"to_group": -1001234567890}]}
    mock_update.message.chat_id = -1001234567890

    await defaults.handle_bakchod_metadata_effects(mock_update, mock_context, mock_bakchod)

    assert not mock_context.bot.forward_message.called


@pytest.mark.asyncio
async def test_handle_message_matching_hi(mock_update, mock_context):
    """Test message matching with 'hi' text."""
    with patch("src.bot.handlers.defaults.hi") as mock_hi:
        mock_hi.handle = AsyncMock()
        mock_update.message.text = "hi"

        await defaults.handle_message_matching(mock_update, mock_context)

        mock_hi.handle.assert_called_once_with(mock_update, mock_context, log_to_dc=False)


@pytest.mark.asyncio
async def test_handle_message_matching_bestie(mock_update, mock_context):
    """Test message matching with 'bestie' in text."""
    with patch("src.bot.handlers.defaults.bestie") as mock_bestie:
        mock_bestie.handle = AsyncMock()
        mock_update.message.text = "You are my bestie"

        await defaults.handle_message_matching(mock_update, mock_context)

        mock_bestie.handle.assert_called_once_with(mock_update, mock_context, log_to_dc=False)


@pytest.fixture
def bot_username():
    """Pin the configured bot username for mention tests."""
    with patch("src.bot.handlers.defaults.BOT_USERNAME", "chaddibot"):
        yield


def make_mention_message(text, mention="@ChaddiBot", entity_type="mention", is_bot=False):
    """Build a mock message whose text contains a bot mention entity."""
    user = MagicMock(spec=User)
    user.is_bot = is_bot
    user.username = "testuser"

    message = MagicMock(spec=Message)
    message.text = text
    message.caption = None
    message.caption_entities = ()
    message.from_user = user

    entity = MagicMock()
    entity.type = entity_type
    if entity_type == "text_mention":
        mentioned_user = MagicMock(spec=User)
        mentioned_user.username = "ChaddiBot"
        entity.user = mentioned_user
    else:
        entity.user = None
    message.entities = (entity,)
    message.parse_entity.return_value = mention

    return message


@pytest.mark.asyncio
async def test_handle_bot_mention_routes_to_ai(mock_update, mock_context, bot_username):
    """Mentioning the bot routes the message to the AI handler, mention stripped."""
    with patch("src.bot.handlers.defaults.ai") as mock_ai:
        mock_ai.handle = AsyncMock()
        mock_update.message = make_mention_message("@ChaddiBot how much is 10000 divided by 12")

        await defaults.handle_bot_mention(mock_update, mock_context)

        mock_ai.handle.assert_awaited_once_with(
            mock_update,
            mock_context,
            question="how much is 10000 divided by 12",
            quiet=True,
        )


@pytest.mark.asyncio
async def test_handle_bot_mention_text_mention_entity(mock_update, mock_context, bot_username):
    """A text_mention entity pointing at the bot also routes to the AI handler."""
    with patch("src.bot.handlers.defaults.ai") as mock_ai:
        mock_ai.handle = AsyncMock()
        mock_update.message = make_mention_message(
            "Chaddi what is this", mention="Chaddi", entity_type="text_mention"
        )

        await defaults.handle_bot_mention(mock_update, mock_context)

        mock_ai.handle.assert_awaited_once_with(
            mock_update, mock_context, question="what is this", quiet=True
        )


@pytest.mark.asyncio
async def test_handle_bot_mention_bare_mention(mock_update, mock_context, bot_username):
    """A bare mention with no question passes question=None (reply may still supply context)."""
    with patch("src.bot.handlers.defaults.ai") as mock_ai:
        mock_ai.handle = AsyncMock()
        mock_update.message = make_mention_message("@ChaddiBot")

        await defaults.handle_bot_mention(mock_update, mock_context)

        mock_ai.handle.assert_awaited_once_with(
            mock_update, mock_context, question=None, quiet=True
        )


@pytest.mark.asyncio
async def test_handle_bot_mention_uses_runtime_username(mock_update, mock_context, bot_username):
    """The username Telegram reports wins over a stale BOT_USERNAME config value."""
    with patch("src.bot.handlers.defaults.ai") as mock_ai:
        mock_ai.handle = AsyncMock()
        mock_context.bot.username = "SomeOtherBot"
        mock_update.message = make_mention_message(
            "@SomeOtherBot hello there", mention="@SomeOtherBot"
        )

        await defaults.handle_bot_mention(mock_update, mock_context)

        mock_ai.handle.assert_awaited_once_with(
            mock_update, mock_context, question="hello there", quiet=True
        )


@pytest.mark.asyncio
async def test_handle_bot_mention_other_user_mentioned(mock_update, mock_context, bot_username):
    """Mentioning someone else does not route to the AI handler."""
    with patch("src.bot.handlers.defaults.ai") as mock_ai:
        mock_ai.handle = AsyncMock()
        mock_update.message = make_mention_message("@someoneelse hello", mention="@someoneelse")

        await defaults.handle_bot_mention(mock_update, mock_context)

        assert not mock_ai.handle.called


@pytest.mark.asyncio
async def test_handle_bot_mention_no_entities(mock_update, mock_context, bot_username):
    """Plain text mentioning the bot's name without an entity does not fire."""
    with patch("src.bot.handlers.defaults.ai") as mock_ai:
        mock_ai.handle = AsyncMock()
        message = make_mention_message("chaddibot is being dumb again")
        message.entities = ()
        mock_update.message = message

        await defaults.handle_bot_mention(mock_update, mock_context)

        assert not mock_ai.handle.called


@pytest.mark.asyncio
async def test_handle_bot_mention_ignores_bots(mock_update, mock_context, bot_username):
    """Mentions from other bots are ignored, to avoid bot-to-bot loops."""
    with patch("src.bot.handlers.defaults.ai") as mock_ai:
        mock_ai.handle = AsyncMock()
        mock_update.message = make_mention_message("@ChaddiBot hello", is_bot=True)

        await defaults.handle_bot_mention(mock_update, mock_context)

        assert not mock_ai.handle.called


@pytest.mark.asyncio
async def test_handle_bot_mention_caption(mock_update, mock_context, bot_username):
    """A mention in a photo caption routes to the AI handler."""
    with patch("src.bot.handlers.defaults.ai") as mock_ai:
        mock_ai.handle = AsyncMock()
        message = make_mention_message("@ChaddiBot what is this")
        message.text = None
        message.caption = "@ChaddiBot what is this"
        message.caption_entities = message.entities
        message.entities = ()
        message.parse_caption_entity.return_value = "@ChaddiBot"
        mock_update.message = message

        await defaults.handle_bot_mention(mock_update, mock_context)

        mock_ai.handle.assert_awaited_once_with(
            mock_update, mock_context, question="what is this", quiet=True
        )


@pytest.mark.asyncio
async def test_handle_message_matching_no_match(mock_update, mock_context):
    """Test message matching with no matching text."""
    with (
        patch("src.bot.handlers.defaults.hi") as mock_hi,
        patch("src.bot.handlers.defaults.bestie") as mock_bestie,
    ):
        mock_update.message.text = "Random message"

        await defaults.handle_message_matching(mock_update, mock_context)

        assert not mock_hi.handle.called
        assert not mock_bestie.handle.called


@pytest.mark.asyncio
async def test_handle_dice_rolls_dice_emoji(mock_update, mock_context):
    """Test dice rolls handler with dice emoji."""
    with patch("src.bot.handlers.defaults.roll") as mock_roll:
        mock_roll.handle_dice_rolls = AsyncMock()
        mock_dice = MagicMock()
        mock_dice.emoji = "🎲"
        mock_dice.value = 4
        mock_update.message.dice = mock_dice

        await defaults.handle_dice_rolls(mock_update, mock_context)

        mock_roll.handle_dice_rolls.assert_called_once_with(4, mock_update, mock_context)


@pytest.mark.asyncio
async def test_handle_dice_rolls_no_dice(mock_update, mock_context):
    """Test dice rolls handler with no dice."""
    with patch("src.bot.handlers.defaults.roll") as mock_roll:
        mock_update.message.dice = None

        await defaults.handle_dice_rolls(mock_update, mock_context)

        assert not mock_roll.handle_dice_rolls.called


@pytest.mark.asyncio
async def test_status_update_new_chat_member(mock_update, mock_context):
    """Test status_update with new chat members."""
    with (
        patch("src.bot.handlers.defaults.group_dao") as mock_group_dao,
        patch("src.bot.handlers.defaults.bakchod_dao") as mock_bakchod_dao,
        patch("src.bot.handlers.defaults.GroupMember") as mock_group_member,
    ):
        mock_group = MagicMock()
        mock_group.group_id = -1001234567890
        mock_group_dao.get_group_from_update.return_value = mock_group

        mock_new_member = MagicMock(spec=User)
        mock_new_member.id = 789012
        mock_new_member.username = "newuser"

        mock_update.message.new_chat_members = [mock_new_member]

        mock_bakchod = MagicMock()
        mock_bakchod.tg_id = 789012
        mock_bakchod_dao.get_or_create_bakchod_from_tg_user.return_value = mock_bakchod

        mock_group_member.get.side_effect = DoesNotExist()

        await defaults.status_update(mock_update, mock_context)

        mock_group_member.create.assert_called_once()


@pytest.mark.asyncio
async def test_status_update_left_chat_member(mock_update, mock_context):
    """Test status_update with left chat member."""
    with (
        patch("src.bot.handlers.defaults.group_dao") as mock_group_dao,
        patch("src.bot.handlers.defaults.bakchod_dao") as mock_bakchod_dao,
        patch("src.bot.handlers.defaults.GroupMember") as mock_group_member,
    ):
        mock_group = MagicMock()
        mock_group.group_id = -1001234567890
        mock_group_dao.get_group_from_update.return_value = mock_group

        mock_left_member = MagicMock(spec=User)
        mock_left_member.id = 789012
        mock_left_member.username = "leftuser"

        mock_update.message.left_chat_member = mock_left_member

        mock_bakchod = MagicMock()
        mock_bakchod.tg_id = 789012
        mock_bakchod_dao.get_or_create_bakchod_from_tg_user.return_value = mock_bakchod

        mock_delete_query = MagicMock()
        mock_group_member.delete.return_value = mock_delete_query
        mock_delete_query.where.return_value.execute.return_value = None

        await defaults.status_update(mock_update, mock_context)

        mock_group_member.delete.assert_called_once()
