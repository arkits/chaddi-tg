import json
import random
import re
import traceback
from collections import defaultdict, deque

from loguru import logger
from rake_nltk import Rake
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.domain import config, dc, util

app_config = config.get_config()

BOT_USERNAME = app_config.get("TELEGRAM", "BOT_USERNAME")

mom_response_blacklist = [BOT_USERNAME]

COMMAND_COST = 200

rake = Rake()

with open("resources/preposition-to-verb-map.json") as f:
    preposition_to_verb_map = json.loads(f.read())

# Verbs that are grammatically fine but comedically dead - "@bakchod needed your mom
# last night" is not a joke. Filtered out before we pick a verb to build the joke on.
BORING_VERBS = {
    "be",
    "have",
    "do",
    "get",
    "go",
    "say",
    "tell",
    "know",
    "think",
    "want",
    "need",
    "let",
    "use",
    "come",
    "seem",
    "look",
    "mean",
}

# Things that tokenize as nouns/proper-nouns but read as garbage in a punchline
URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")
MENTION_PATTERN = re.compile(r"@\w+")
COMMAND_PATTERN = re.compile(r"(?:^|\s)/\w+(?:@\w+)?")

# A joke needs something to chew on - one-word replies just produce noise
MIN_JOKEABLE_WORDS = 2

# Remember the last few punchlines per chat so /mom doesn't repeat itself
RECENT_JOKE_MEMORY = 5
MAX_GENERATION_ATTEMPTS = 3
recent_jokes = defaultdict(lambda: deque(maxlen=RECENT_JOKE_MEMORY))


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        dc.log_command_usage("mom", update)

        # Fast fail if a user didn't reply to another user
        if update.message.reply_to_message is None:
            logger.debug(
                "[mom] user didn't reply to another user",
            )
            await update.message.reply_text(
                "Try replying to someone with `/mom`", parse_mode=ParseMode.MARKDOWN
            )
            return

        initiator_user = update.message.from_user
        if initiator_user is None:
            logger.error("[mom] initiator_user was None!")
            return

        # Check if Bakchod has enough rokda to do a /mom...
        if not util.paywall_user(initiator_user.id, COMMAND_COST):
            await update.message.reply_text(
                f"Sorry! You don't have enough ₹okda! Each /mom costs {COMMAND_COST} ₹okda."
            )
            return

        # Extract the protagonist. The protagonist <verb>'d your <victim> last night
        protagonist = util.extract_pretty_name_from_tg_user(update.message.from_user)

        # Extract the recipient - Telegram User who shall receive the insult
        if update.message.reply_to_message.from_user is None:
            sticker_to_send = "CAADAQADrAEAAp6M4Ahtgp9JaiLJPxYE"
            await update.message.reply_sticker(sticker=sticker_to_send)
            return

        recipient = update.message.reply_to_message.from_user

        # Check if recipient is in the backlist
        if recipient.username in mom_response_blacklist:
            logger.debug(
                "[mom] recipient.username={} in mom_response_blacklist",
                util.extract_pretty_name_from_tg_user(recipient),
            )

            if recipient.username == BOT_USERNAME:
                # Don't insult Chaddi!
                sticker_to_send = "CAADAQADrAEAAp6M4Ahtgp9JaiLJPxYE"
                await update.message.reply_sticker(sticker=sticker_to_send)
                return
            else:
                # Protect the users in the blacklist
                await update.message.reply_text(
                    f"{util.extract_pretty_name_from_tg_user(recipient)} is protected by a 👁️ Nazar Raksha Kavach"
                )
                return

        else:
            logger.debug(
                "[mom] recipient.username={} was not in mom_response_blacklist={}",
                recipient.username,
                mom_response_blacklist,
            )

        # Extract the message for base the insult on
        message = extract_target_message(update)
        if message is None:
            logger.info("[mom] message was None!")
            sticker_to_send = "CAADAQADrAEAAp6M4Ahtgp9JaiLJPxYE"
            await update.message.reply_sticker(sticker=sticker_to_send)
            return

        response = generate_response(message, protagonist, update.message.chat_id)

        if random.random() > 0.01:
            await update.message.reply_to_message.reply_text(response)
        else:
            # User has chance to get protected
            await update.message.reply_text(
                f"{util.extract_pretty_name_from_tg_user(recipient)} is protected by a 👁️ Nazar Raksha Kavach"
            )

        return

    except Exception as e:
        logger.error(
            "Caught Error in mom.handle - {} \n {}",
            e,
            traceback.format_exc(),
        )
        return


def generate_response(message, protagonist, chat_id=None):
    """Generate a punchline, rerolling if we just told the same one in this chat."""

    response = None

    for _ in range(MAX_GENERATION_ATTEMPTS):
        response = None

        if random.random() < 0.20:
            logger.info(
                "[mom] generating response with rake - protagonist='{}' message='{}'",
                protagonist,
                message,
            )
            response = rake_joke(message, protagonist)

        # rake_joke returns None when it can't find a usable phrase - fall through
        if response is None:
            logger.info(
                "[mom] generating response with spacy - protagonist='{}' message='{}'",
                protagonist,
                message,
            )
            response = spacy_joke(message, protagonist)

        if chat_id is None or response not in recent_jokes[chat_id]:
            break

        logger.debug("[mom] response='{}' was a repeat, rerolling", response)

    if chat_id is not None:
        recent_jokes[chat_id].append(response)

    return response


def extract_target_message(update: Update):
    target_message = None

    if update.message.reply_to_message:
        # The invoker invoked the command by replying to a message
        if update.message.reply_to_message.text:
            target_message = update.message.reply_to_message.text

        # The invoker invoked the command by replying with a caption
        elif update.message.reply_to_message.caption:
            target_message = update.message.reply_to_message.caption

    return target_message


def clean_sentence(sentence):
    """Strip out the bits that spaCy happily tags but that read as garbage in a joke."""

    if sentence is None:
        return None

    cleaned = URL_PATTERN.sub(" ", sentence)
    cleaned = MENTION_PATTERN.sub(" ", cleaned)
    cleaned = COMMAND_PATTERN.sub(" ", cleaned)
    cleaned = " ".join(cleaned.split())

    return cleaned if cleaned else None


def is_wordlike(text):
    """True if the token could plausibly sit in an English sentence (no emoji, no digits)."""

    return len(text) > 1 and re.search(r"[a-zA-Z]", text) is not None


def rake_joke(message, protagonist):
    message = clean_sentence(message)
    if message is None:
        return None

    # Extract a phrase from the message
    rake.extract_keywords_from_text(message)
    phrases = rake.get_ranked_phrases()

    # Messages made entirely of stopwords give us nothing to work with
    if not phrases:
        logger.info("[mom] rake found no phrases in message='{}'", message)
        return None

    # Long phrases drown the punchline - keep it snappy
    phrase = " ".join(phrases[0].split()[:4])

    # Extract a random verb from the phrase
    random_verb = util.extract_magic_word(phrase)
    if random_verb is None:
        return None

    # Derive a preposition that goes along
    if random_verb in preposition_to_verb_map:
        # This will be an array
        prepositions = preposition_to_verb_map.get(random_verb)
    else:
        prepositions = ["in", "on", "with"]

    # Extract a random preposition
    preposition = random.choice(prepositions)

    # If the magic word is a genuine verb, let it carry the joke. Otherwise keep the
    # raw phrase - past-tensing a noun just invents words like "dayed".
    verb_past = lookup_verb_past(random_verb.lower())
    subject = verb_past if verb_past is not None else phrase

    return f"{protagonist} {subject} {preposition} your mom last night"


def spacy_joke(message, protagonist):
    return joke_mom(message, protagonist)


# !! SEXISM !!
# make a bad joke about it
def joke_mom(sentence, protagonist, force=False):
    target = "your mom"

    if not force and random.random() > 0.95:
        # flip the joke occasionally
        target, protagonist = protagonist, target

    if sentence is None:
        return f"{protagonist}, kripaya aapna aadhaar link kare"

    sentence = clean_sentence(sentence)

    # Nothing survived cleaning, or the message was too thin to joke about
    if sentence is None or len(sentence.split()) < MIN_JOKEABLE_WORDS:
        return random_reply(protagonist)

    # extract parts of speech and generate insults
    verb = get_verb(sentence)
    if verb is not None:
        return f"{protagonist} {verb} {target} last night"

    adjective = get_pos(sentence, "ADJ")
    if adjective is not None:
        # works whether the adjective is a compliment or an insult
        return f"{protagonist} is {adjective}, {target} told me"

    propn = get_pos(sentence, "PROPN")
    if propn is not None:
        past = get_verb_past(propn.lower())
        return f"{protagonist} {past} {target} last night"

    return random_reply(protagonist)


# return a random relevant part of speech tag
def get_pos(sentence, pos):
    doc = util.get_nlp()(sentence)

    candidates = [token.text for token in doc if token.pos_ == pos and is_wordlike(token.text)]

    if not candidates:
        return None

    return random.choice(candidates)


def has_object(token):
    """True if the verb already takes a direct object, i.e. it's transitive."""

    try:
        return any(child.dep_ in ("dobj", "obj", "dative") for child in token.children)
    except TypeError:
        return False


# return a verb from the sentence, preferring ones that make the joke work
def get_verb(sentence):
    doc = util.get_nlp()(sentence)

    transitive = []
    other = []

    for token in doc:
        if token.pos_ != "VERB":
            continue

        lemma = str(token.lemma_).lower()

        # "@bakchod was your mom last night" isn't a joke
        if lemma in BORING_VERBS or not is_wordlike(lemma):
            continue

        if has_object(token):
            transitive.append(lemma)
        else:
            other.append(lemma)

    # "X <verb>'d your mom" only works for verbs that can take an object -
    # intransitives give us "@bakchod went your mom last night"
    verbs = transitive or other

    if verbs:
        return get_verb_past(random.choice(verbs))

    noun = get_pos(sentence, "NOUN")

    if noun is not None:
        # only use the noun if it genuinely has a verb form, otherwise we end up
        # inventing words like "tableed"
        known_past = lookup_verb_past(noun.lower())
        if known_past is not None:
            return known_past

    return None


def lookup_verb_past(verb):
    """Look the verb up in the irregular-past table, returning None if it isn't a verb."""

    verb_past_lookup = util.get_verb_past_lookup()

    # the resource file wraps the map in a single-element list
    if isinstance(verb_past_lookup, list):
        verb_past_lookup = verb_past_lookup[0] if verb_past_lookup else {}

    return verb_past_lookup.get(verb)


# return simple past form of verb
def get_verb_past(verb):
    verb = verb.lower()

    known_past = lookup_verb_past(verb)
    if known_past is not None:
        return known_past

    return regular_past(verb)


def regular_past(verb):
    """Best-effort regular past tense for verbs missing from the lookup table."""

    if verb.endswith("ed"):
        return verb

    if verb.endswith("e"):
        return verb + "d"

    # carry -> carried, but stay -> stayed
    if verb.endswith("y") and len(verb) > 2 and verb[-2] not in "aeiou":
        return verb[:-1] + "ied"

    # single-syllable CVC doubles the final consonant: stan -> stanned
    if (
        len(verb) > 2
        and verb[-1] not in "aeiouwxy"
        and verb[-2] in "aeiou"
        and verb[-3] not in "aeiou"
        and len(re.findall(r"[aeiou]+", verb)) == 1
    ):
        return verb + verb[-1] + "ed"

    return verb + "ed"


def random_reply(protagonist):
    replies = [
        f"{protagonist} should get a life",
        "haaaaaaaaaaaaaaaat",
        "bhaaaaaaaaaaaaaaak",
        "arrey isko hatao re",
        "haat bsdk",
        "bhaak bsdk",
    ]

    return random.choice(replies)
