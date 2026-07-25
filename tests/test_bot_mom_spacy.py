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


@pytest.mark.asyncio
async def test_handle_success_spacy_joke(mock_update, mock_context):
    """Test mom handler with successful spacy joke generation."""
    with (
        patch("src.bot.handlers.mom_spacy.dc"),
        patch("src.bot.handlers.mom_spacy.util") as mock_util,
        patch("src.bot.handlers.mom_spacy.random.random") as mock_random,
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
        patch("src.bot.handlers.mom_spacy.get_verb", return_value=None),
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
        patch("src.bot.handlers.mom_spacy.get_verb", return_value=None),
        patch("src.bot.handlers.mom_spacy.get_pos") as mock_get_pos,
        patch("src.bot.handlers.mom_spacy.get_verb_past", return_value="tested"),
        patch("src.bot.handlers.mom_spacy.random") as mock_random,
    ):
        mock_get_pos.side_effect = lambda x, y: None if y == "ADJ" else "Test"
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


def test_get_verb_noun_with_verb_form():
    """A noun that has a real verb form is used as the verb."""
    with (
        patch("src.bot.handlers.mom_spacy.util") as mock_util,
        patch("src.bot.handlers.mom_spacy.lookup_verb_past", return_value="tested"),
        patch("src.bot.handlers.mom_spacy.get_pos", return_value="test"),
    ):
        mock_nlp = MagicMock()
        mock_token = MagicMock()
        mock_token.pos_ = "NOUN"
        mock_nlp.return_value = [mock_token]
        mock_util.get_nlp.return_value = mock_nlp

        result = mom_spacy.get_verb("User test message")

        assert result == "tested"


def test_get_verb_noun_without_verb_form():
    """A noun with no verb form must not be turned into a fake verb."""
    with (
        patch("src.bot.handlers.mom_spacy.util") as mock_util,
        patch("src.bot.handlers.mom_spacy.lookup_verb_past", return_value=None),
        patch("src.bot.handlers.mom_spacy.get_pos", return_value="table"),
    ):
        mock_nlp = MagicMock()
        mock_token = MagicMock()
        mock_token.pos_ = "NOUN"
        mock_nlp.return_value = [mock_token]
        mock_util.get_nlp.return_value = mock_nlp

        result = mom_spacy.get_verb("the table message")

        assert result is None


def test_get_verb_skips_boring_verbs():
    """Verbs like 'be' and 'need' don't make a joke and should be ignored."""
    with patch("src.bot.handlers.mom_spacy.util") as mock_util:
        mock_nlp = MagicMock()

        boring = MagicMock()
        boring.pos_ = "VERB"
        boring.lemma_ = "need"
        boring.children = []

        interesting = MagicMock()
        interesting.pos_ = "VERB"
        interesting.lemma_ = "roast"
        interesting.children = []

        mock_nlp.return_value = [boring, interesting]
        mock_util.get_nlp.return_value = mock_nlp
        mock_util.get_verb_past_lookup.return_value = [{"roast": "roasted"}]

        result = mom_spacy.get_verb("I need to roast that")

        assert result == "roasted"


def test_get_verb_prefers_transitive():
    """A verb that already takes an object beats an intransitive one."""
    with patch("src.bot.handlers.mom_spacy.util") as mock_util:
        mock_nlp = MagicMock()

        child = MagicMock()
        child.dep_ = "dobj"

        transitive = MagicMock()
        transitive.pos_ = "VERB"
        transitive.lemma_ = "roast"
        transitive.children = [child]

        intransitive = MagicMock()
        intransitive.pos_ = "VERB"
        intransitive.lemma_ = "sleep"
        intransitive.children = []

        mock_nlp.return_value = [intransitive, transitive]
        mock_util.get_nlp.return_value = mock_nlp
        mock_util.get_verb_past_lookup.return_value = [{"roast": "roasted", "sleep": "slept"}]

        # run it a few times - the intransitive verb must never win
        for _ in range(10):
            assert mom_spacy.get_verb("I sleep and roast him") == "roasted"


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

        result = mom_spacy.get_verb_past("yeet")

        assert result == "yeeted"


@pytest.mark.parametrize(
    "verb,expected",
    [
        ("stan", "stanned"),  # single-syllable CVC doubles
        ("chat", "chatted"),
        ("carry", "carried"),  # consonant + y
        ("stay", "stayed"),  # vowel + y
        ("vibe", "vibed"),
        ("yeet", "yeeted"),  # not CVC, no doubling
        ("visit", "visited"),  # multi-syllable, no doubling
    ],
)
def test_regular_past_morphology(verb, expected):
    """Verbs missing from the lookup table still get a plausible past tense."""
    assert mom_spacy.regular_past(verb) == expected


@pytest.mark.asyncio
async def test_handle_protected_reply_does_not_crash(mock_update, mock_context):
    """The rare 'protected' branch must send a real message, not blow up on a User object."""
    with (
        patch("src.bot.handlers.mom_spacy.dc"),
        patch("src.bot.handlers.mom_spacy.util") as mock_util,
        patch("src.bot.handlers.mom_spacy.random.random", return_value=0.0),
    ):
        mock_util.paywall_user.return_value = True
        mock_util.extract_pretty_name_from_tg_user.return_value = "@replyuser"

        reply_user = MagicMock(spec=User)
        reply_user.id = 789012
        reply_user.username = "replyuser"

        reply_message = MagicMock(spec=Message)
        reply_message.from_user = reply_user
        reply_message.text = "Test message"

        mock_update.message.reply_to_message = reply_message

        with patch.object(mom_spacy, "generate_response", return_value="joke"):
            await mom_spacy.handle(mock_update, mock_context)

        # random.random() == 0.0 is not > 0.01, so we take the protected branch
        mock_update.message.reply_text.assert_called_once()
        assert "Nazar Raksha Kavach" in mock_update.message.reply_text.call_args[0][0]


def test_rake_joke_returns_none_for_stopword_only_message():
    """rake finds no phrases in an all-stopword message - must not raise IndexError."""
    assert mom_spacy.rake_joke("what is it", "@user") is None


def test_generate_response_falls_back_when_rake_fails():
    """A message rake can't handle still produces a joke via spacy."""
    with patch("src.bot.handlers.mom_spacy.random.random", return_value=0.0):
        # random < 0.20 picks the rake path, which returns None for this message
        response = mom_spacy.generate_response("what is it", "@user", chat_id=None)

        assert response is not None
        assert response != ""


def test_generate_response_avoids_repeating_itself():
    """The same message twice in a chat shouldn't give the exact same punchline."""
    mom_spacy.recent_jokes.pop(-1, None)

    seen = set()
    for _ in range(5):
        seen.add(mom_spacy.generate_response("he roasted the chai", "@user", chat_id=-1))

    mom_spacy.recent_jokes.pop(-1, None)

    assert len(seen) > 1


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("check https://x.com/foo out", "check out"),
        ("@someone is wrong", "is wrong"),
        ("/mom@chaddi_bot hello", "hello"),
        ("   ", None),
    ],
)
def test_clean_sentence(raw, expected):
    """URLs, mentions and commands are stripped before we tag parts of speech."""
    assert mom_spacy.clean_sentence(raw) == expected


def test_joke_mom_ignores_urls():
    """A URL must never end up as the verb in the punchline."""
    result = mom_spacy.joke_mom("https://x.com/foo", "@user", force=True)

    assert "http" not in result


def test_joke_mom_short_message_falls_back():
    """One-word messages give a canned reply rather than a nonsense joke."""
    result = mom_spacy.joke_mom("lmao", "@user", force=True)

    assert "your mom last night" not in result


def test_random_reply():
    """Test random_reply function."""
    result = mom_spacy.random_reply("User")

    assert result is not None
    assert len(result) > 0
