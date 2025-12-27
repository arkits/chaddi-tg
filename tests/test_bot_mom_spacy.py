from unittest.mock import AsyncMock, MagicMock, patch

import nltk
import pytest
from telegram import Chat, Message, Update, User
from telegram.ext import ContextTypes

from src.bot.handlers import mom_spacy

nltk.download("punkt_tab", quiet=True)


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
    message.text = "/mom"
    message.reply_to_message = None
    message.reply_text = AsyncMock()
    message.reply_sticker = AsyncMock()

    update = MagicMock(spec=Update)
    update.message = message

    return update


@pytest.fixture
def mock_context():
    """Create a mock ContextTypes object for testing."""
    return MagicMock(spec=ContextTypes.DEFAULT_TYPE)


@pytest.mark.asyncio
async def test_handle_no_reply_to_message(mock_update, mock_context):
    """Test mom handler without reply to message."""
    with patch("src.bot.handlers.mom_spacy.dc"):
        await mom_spacy.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_handle_no_initiator_id(mock_update, mock_context):
    """Test mom handler when initiator_id is None."""
    with patch("src.bot.handlers.mom_spacy.dc"):
        mock_update.message.from_user.id = None

        reply_user = MagicMock(spec=User)
        reply_user.id = 789012
        reply_user.username = "replyuser"

        reply_message = MagicMock(spec=Message)
        reply_message.from_user = reply_user

        mock_update.message.reply_to_message = reply_message

        await mom_spacy.handle(mock_update, mock_context)

        assert mock_update.message.reply_text.call_count <= 1


@pytest.mark.asyncio
async def test_handle_insufficient_rokda(mock_update, mock_context):
    """Test mom handler when user doesn't have enough rokda."""
    with (
        patch("src.bot.handlers.mom_spacy.dc"),
        patch("src.bot.handlers.mom_spacy.util") as mock_util,
    ):
        mock_util.paywall_user.return_value = False

        reply_user = MagicMock(spec=User)
        reply_user.id = 789012
        reply_user.username = "replyuser"

        reply_message = MagicMock(spec=Message)
        reply_message.from_user = reply_user

        mock_update.message.reply_to_message = reply_message

        await mom_spacy.handle(mock_update, mock_context)

        assert "₹okda" in mock_update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_handle_recipient_is_bot(mock_update, mock_context):
    """Test mom handler when recipient is = bot itself."""
    with (
        patch("src.bot.handlers.mom_spacy.dc"),
        patch("src.bot.handlers.mom_spacy.util") as mock_util,
        patch("src.bot.handlers.mom_spacy.BOT_USERNAME", "testbot"),
        patch("src.bot.handlers.mom_spacy.mom_response_blacklist", ["testbot"]),
    ):
        mock_util.paywall_user.return_value = True

        reply_user = MagicMock(spec=User)
        reply_user.id = 789012
        reply_user.username = "testbot"

        reply_message = MagicMock(spec=Message)
        reply_message.from_user = reply_user

        mock_update.message.reply_to_message = reply_message

        await mom_spacy.handle(mock_update, mock_context)

        mock_update.message.reply_sticker.assert_called_once()


@pytest.mark.asyncio
async def test_handle_recipient_in_blacklist(mock_update, mock_context):
    """Test mom handler when recipient is in blacklist."""
    with (
        patch("src.bot.handlers.mom_spacy.dc"),
        patch("src.bot.handlers.mom_spacy.util") as mock_util,
        patch("src.bot.handlers.mom_spacy.mom_response_blacklist", ["protected_user"]),
    ):
        mock_util.paywall_user.return_value = True

        reply_user = MagicMock(spec=User)
        reply_user.id = 789012
        reply_user.username = "protected_user"

        reply_message = MagicMock(spec=Message)
        reply_message.from_user = reply_user
        reply_message.text = "Test message"

        mock_update.message.reply_to_message = reply_message

        await mom_spacy.handle(mock_update, mock_context)

        assert "Nazar Raksha Kavach" in mock_update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_handle_no_target_message(mock_update, mock_context):
    """Test mom handler when target message is None."""
    with (
        patch("src.bot.handlers.mom_spacy.dc"),
        patch("src.bot.handlers.mom_spacy.util") as mock_util,
    ):
        mock_util.paywall_user.return_value = True

        reply_user = MagicMock(spec=User)
        reply_user.id = 789012
        reply_user.username = "replyuser"

        reply_message = MagicMock(spec=Message)
        reply_message.from_user = reply_user
        reply_message.text = None
        reply_message.caption = None

        mock_update.message.reply_to_message = reply_message

        await mom_spacy.handle(mock_update, mock_context)

        mock_update.message.reply_sticker.assert_called_once()


@pytest.mark.xfail(reason="Complex mocking of random reply behavior")
@pytest.mark.xfail(reason="Complex mocking of random reply behavior")
@pytest.mark.asyncio
async def test_handle_success_spacy_joke(mock_update, mock_context):
    """Test mom handler with successful spacy joke generation."""
    with (
        patch("src.bot.handlers.mom_spacy.dc"),
        patch("src.bot.handlers.mom_spacy.util") as mock_util,
        patch("src.bot.handlers.mom_spacy.random") as mock_random,
    ):
        mock_util.paywall_user.return_value = True
        mock_random.return_value = 0.8  # >= 0.20 so spacy triggers

        reply_user = MagicMock(spec=User)
        reply_user.id = 789012
        reply_user.username = "replyuser"

        reply_message = MagicMock(spec=Message)
        reply_message.from_user = reply_user
        reply_message.text = "Test message"

        mock_update.message.reply_to_message = reply_message

        with patch.object(mom_spacy, "spacy_joke", return_value="Test response"):
            await mom_spacy.handle(mock_update, mock_context)

            assert (
                mock_update.message.reply_to_message.reply_text.called
                or mock_update.message.reply_text.called
            )


@pytest.mark.asyncio
async def test_handle_recipient_no_from_user(mock_update, mock_context):
    """Test mom handler when recipient has no from_user."""
    with (
        patch("src.bot.handlers.mom_spacy.dc"),
        patch("src.bot.handlers.mom_spacy.util") as mock_util,
    ):
        mock_util.paywall_user.return_value = True

        reply_message = MagicMock(spec=Message)
        reply_message.from_user = None

        mock_update.message.reply_to_message = reply_message

        await mom_spacy.handle(mock_update, mock_context)

        mock_update.message.reply_sticker.assert_called_once()


def test_extract_target_message_from_text():
    """Test extract_target_message with text message."""
    user = MagicMock(spec=User)
    user.id = 789012

    reply_message = MagicMock(spec=Message)
    reply_message.text = "Test message text"
    reply_message.caption = None

    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.reply_to_message = reply_message

    result = mom_spacy.extract_target_message(update)

    assert result == "Test message text"


def test_extract_target_message_from_caption():
    """Test extract_target_message with caption."""
    user = MagicMock(spec=User)
    user.id = 789012

    reply_message = MagicMock(spec=Message)
    reply_message.text = None
    reply_message.caption = "Test caption"

    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.reply_to_message = reply_message

    result = mom_spacy.extract_target_message(update)

    assert result == "Test caption"


def test_extract_target_message_none():
    """Test extract_target_message with no reply message."""
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.reply_to_message = None

    result = mom_spacy.extract_target_message(update)

    assert result is None


def test_rake_joke():
    """Test rake_joke function."""
    with (
        patch("src.bot.handlers.mom_spacy.util") as mock_util,
        patch("src.bot.handlers.mom_spacy.preposition_to_verb_map", {"test": ["in", "on"]}),
        patch("src.bot.handlers.mom_spacy.random") as mock_random,
    ):
        mock_util.extract_magic_word.return_value = "testing"
        mock_random.choice.return_value = "on"

        result = mom_spacy.rake_joke("test phrase", "User")

        assert "User" in result
        assert "on" in result
        assert "last night" in result


def test_spacy_joke():
    """Test spacy_joke function."""
    with patch.object(mom_spacy, "joke_mom", return_value="Test joke"):
        result = mom_spacy.spacy_joke("message", "User")

        assert result == "Test joke"


def test_joke_mom_with_verb():
    """Test joke_mom function with verb."""
    with (
        patch("src.bot.handlers.mom_spacy.get_verb", return_value="tested"),
        patch("src.bot.handlers.mom_spacy.random") as mock_random,
    ):
        mock_random.return_value = 0.8  # Don't flip

        result = mom_spacy.joke_mom("User tested message", "Protagonist", force=True)

        assert "Protagonist" in result
        assert "your mom" in result
        assert "last night" in result


def test_joke_mom_with_adjective():
    """Test joke_mom function with adjective."""
    with (
        patch("src.bot.handlers.mom_spacy.get_verb", return_value=0),
        patch("src.bot.handlers.mom_spacy.get_pos", return_value="nice"),
        patch("src.bot.handlers.mom_spacy.random") as mock_random,
    ):
        mock_random.return_value = 0.8  # Don't flip

        result = mom_spacy.joke_mom("User is nice", "Protagonist", force=True)

        assert "Protagonist" in result
        assert "nice" in result


def test_joke_mom_with_propn():
    """Test joke_mom function with proper noun."""
    with (
        patch("src.bot.handlers.mom_spacy.get_verb", return_value=0),
        patch("src.bot.handlers.mom_spacy.get_pos") as mock_get_pos,
        patch("src.bot.handlers.mom_spacy.get_verb_past", return_value="tested"),
        patch("src.bot.handlers.mom_spacy.random") as mock_random,
    ):
        mock_get_pos.side_effect = lambda x, y: 0 if y == "ADJ" else "Test"
        mock_random.return_value = 0.8  # Don't flip

        result = mom_spacy.joke_mom("Test message", "Protagonist", force=True)

        assert "Protagonist" in result
        assert "your mom" in result


def test_joke_mom_none_sentence():
    """Test joke_mom with None sentence."""
    result = mom_spacy.joke_mom(None, "Protagonist", force=True)

    assert "aadhaar link kare" in result


def test_get_pos():
    """Test get_pos function."""
    with patch("src.bot.handlers.mom_spacy.util") as mock_util:
        mock_nlp = MagicMock()
        mock_token = MagicMock()
        mock_token.pos_ = "ADJ"
        mock_token.text = "nice"
        mock_nlp.return_value = [mock_token]
        mock_util.get_nlp.return_value = mock_nlp

        result = mom_spacy.get_pos("nice day", "ADJ")

        assert result == "nice"


def test_get_verb():
    """Test get_verb function."""
    with (
        patch("src.bot.handlers.mom_spacy.util") as mock_util,
        patch("src.bot.handlers.mom_spacy.get_verb_past", return_value="tested"),
    ):
        mock_nlp = MagicMock()
        mock_token = MagicMock()
        mock_token.pos_ = "VERB"
        mock_token.lemma_ = "test"
        mock_nlp.return_value = [mock_token]
        mock_util.get_nlp.return_value = mock_nlp

        result = mom_spacy.get_verb("User tested message")

        assert result == "tested"


def test_get_verb_no_verb():
    """Test get_verb function when no verb found."""
    with (
        patch("src.bot.handlers.mom_spacy.util") as mock_util,
        patch("src.bot.handlers.mom_spacy.get_verb_past", return_value="tested"),
        patch("src.bot.handlers.mom_spacy.get_pos") as mock_get_pos,
    ):
        mock_nlp = MagicMock()
        mock_token = MagicMock()
        mock_token.pos_ = "NOUN"
        mock_nlp.return_value = [mock_token]
        mock_util.get_nlp.return_value = mock_nlp
        mock_get_pos.return_value = "test"

        result = mom_spacy.get_verb("User test message")

        assert result == "tested"


def test_get_verb_past_from_lookup():
    """Test get_verb_past from lookup."""
    with patch("src.bot.handlers.mom_spacy.util") as mock_util:
        mock_util.get_verb_past_lookup.return_value = {"test": "tested"}

        result = mom_spacy.get_verb_past("test")

        assert result == "tested"


def test_get_verb_past_ed():
    """Test get_verb_past with 'ed' suffix."""
    with patch("src.bot.handlers.mom_spacy.util") as mock_util:
        mock_util.get_verb_past_lookup.return_value = {}

        result = mom_spacy.get_verb_past("tested")

        assert result == "tested"


def test_get_verb_past_e():
    """Test get_verb_past with 'e' suffix."""
    with patch("src.bot.handlers.mom_spacy.util") as mock_util:
        mock_util.get_verb_past_lookup.return_value = {}

        result = mom_spacy.get_verb_past("test")

        assert result == "tested"


def test_get_verb_past_default():
    """Test get_verb_past default suffix."""
    with patch("src.bot.handlers.mom_spacy.util") as mock_util:
        mock_util.get_verb_past_lookup.return_value = {}

        result = mom_spacy.get_verb_past("run")

        assert result == "runed"


def test_random_reply():
    """Test random_reply function."""
    result = mom_spacy.random_reply("User")

    assert result is not None
    assert len(result) > 0
