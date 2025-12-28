import random
import traceback
from datetime import date, timedelta

from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes

from src.domain import dc

vowels = {"a", "e", "i", "o", "u"}


def choose_uniq(exclude, *args):
    item = choose_from(*args)
    while item in exclude:
        item = choose_from(*args)
    return item


def choose_from(*args):
    num_words = sum([len(x) for x in args])
    i = random.randint(0, num_words - 1)
    for _j, x in enumerate(args):
        if i < len(x):
            return x[i]
        i -= len(x)


def sentence_case(sentence, exciting=False):
    sentence = sentence[0].upper() + sentence[1:]

    if sentence[-1] in {".", "!", "?"}:
        return sentence
    elif exciting:
        return sentence + "!"
    else:
        return sentence + "."


def ing_to_ed(word):
    if word[-3:] == "ing":
        return word[:-3] + "ed"
    else:
        return word


def an(word):
    if word[0] in vowels:
        return f"an {word}"
    else:
        return f"a {word}"


planets = ["Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]

stars = ["Proxima Centauri", "Barnard's Star", "Sirius A", "Epsilon Eridani"]

aspects = ["conjunction", "sextile", "square", "trine", "opposition"]

wanky_events = [
    "a large Electromagnetic disturbance",
    "Quantum Flux",
    "the upcoming Solar eclipse",
    "Unusual planetary motion",
]

beginnings = ["arrival", "beginning", "start"]
endings = ["end", "death", "passing"]
time_periods = ["interlude", "period", "week", "day"]

good_feeling_adjs = [
    "romantic",
    "emotional",
    "reflective",
    "irreverent",
    "subversive",
    "spiritual",
    "creative",
    "intellectual",
    "adventurous",
    "enlightening",
    "fantastic",
]

bad_feeling_adjs = ["bitter", "disappointing", "frustrating"]

good_emotive_adjs = ["cathartic", "healing", "mystical"]
bad_emotive_adjs = ["anti-climactic"]

good_degrees = ["ridiculously", "amazingly"]
neutral_degrees = ["a little bit", "fairly", "pretty", "curiously"]
bad_degrees = ["worringly", "distressingly"]

good_feeling_nouns = [
    "love",
    "reflection",
    "romance",
    "enlightenment",
    "joy",
    "desire",
    "creativity",
]

good_emotive_nouns = ["healing", "catharsis", "mysticism", "transcendence", "metamorphisis"]

bad_feeling_nouns = [
    "bitterness",
    "disappointment",
    "sadness",
    "frustration",
    "anger",
    "failure",
    "boredom",
    "tension",
]

bad_emotive_nouns = ["bad luck", "misfortune", "déjà vu"]

prediction_verbs = ["heralds", "marks", "foreshadows", "signifies"]

avoid_list = [
    "shopping",
    "swimming",
    "starchy carbs",
    "engaging strangers in conversation",
    "making too many jokes",
    "eating seafood",
    "rigorous physical activity",
    "operating heavy machinery",
    "staying inside for extended periods of time",
    "alienating your friends",
    "making life-changing decisions",
    "prolonging the inevitable",
    "places of worship",
    "people who are likely to annoy you",
    "drinking heavily this weekend",
]

familiar_people = ["your mother", "your father", "your closest friend", "a family member"]

strange_people = [
    "a priest or minister",
    "a doctor",
    "a lawyer",
    "a mysterious gentleman",
    "a kind older lady",
    "a local public transport identity",
    "a seductive salesperson",
    "an old friend",
    "a washed up celebrity",
    "an attractive celebrity",
    "a homeless man",
    "a homeless woman",
    "a psychic",
    "a convicted criminal",
    "a musician",
    "a musical friend",
    "a mathematical friend",
    "a scientist",
    "a distant relative",
    "the love of your life",
    "your ex",
    "a bearded man",
    "your loudest friend",
    "an acquaintance",
    "someone from high school",
    "someone from university",
    "a reality tv show contestant",
    "a politician",
    "a right-wing politician",
    "a left-wing politician",
]

locations = [
    ("at", "the beach"),
    ("in", "a shopping centre"),
    ("in", "the bush"),
    ("in", "a carpark"),
    ("at", "your house"),
    ("in", "your street"),
    ("near", "where you grew up"),
    ("in", "a club"),
    ("in", "a supermarket"),
    ("at", "a place of learning"),
    ("by", "the side of the road"),
    ("in", "the centre of the city"),
    ("in", "the heart of suburbia"),
    ("on top of", "a building"),
    ("in", "a park"),
    ("in", "a restaurant"),
    ("on", "a bus"),
    ("on", "a train"),
    ("on", "a ferry"),
    ("in", "a waiting room"),
    ("at", "a library"),
]

neutral_discussions = ["discussion", "talk", "conversation", "debate"]

good_discussions = ["chat", "intimate conversation", "chin wag"]

bad_discussions = ["argument", "fight", "altercation", "terse chat", "misunderstanding"]

conversation_topics = [
    "the past",
    "the future",
    "your career",
    "your future",
    "music",
    "a TV show",
    "a film",
    "politics",
    "religion",
    "their feelings",
    "your feelings",
    "their work",
]


def wordlist(name, prefix=""):
    name = prefix + name
    return globals()[name]


def generate():
    mood = "good" if random.random() <= 0.8 else "bad"

    discussion_s = choose_from([relationship_s, encounter_s])
    sentences = [feeling_statement_s, cosmic_implication_s, warning_s, discussion_s]

    k = random.randint(2, 3)
    sentences = random.sample(sentences, k)
    final_text = " ".join(
        [sentence(mood) if sentence != warning_s else warning_s() for sentence in sentences]
    )

    if random.random() <= 0.5 and k == 2:
        final_text += " " + date_prediction_s(mood)

    return final_text


def relationship_s(mood):
    if mood == "good":
        verb = "strengthened"
        talk = "discussion"
    else:
        verb = "strained"
        talk = "argument"

    familiar_people = wordlist("familiar_people")
    conversation_topics = wordlist("conversation_topics")

    person = choose_from(familiar_people)
    topic = choose_from(conversation_topics)
    s = f"Your relationship with {person} may be {verb} "
    s += f"as the result of {an(talk)} about {topic}"

    return sentence_case(s)


def encounter_s(mood):
    familiar_people = wordlist("familiar_people")
    strange_people = wordlist("strange_people")
    locations = wordlist("locations")

    person = choose_from(familiar_people, strange_people)
    location = choose_from(locations)
    preposition = location[0]
    location = location[1]
    s1 = f"You may meet {person} {preposition} {location}."

    discussions = wordlist("neutral_discussions")
    discussions += wordlist("_discussions", prefix=mood)
    feeling_nouns = wordlist("_feeling_nouns", prefix=mood)
    emotive_nouns = wordlist("_emotive_nouns", prefix=mood)
    conversation_topics = wordlist("conversation_topics")

    discussion = choose_from(discussions)
    if random.random() <= 0.5:
        feeling = choose_from(feeling_nouns)
        feeling = f"feelings of {feeling}"
    else:
        feeling = choose_from(emotive_nouns)
    topic = choose_from(conversation_topics)

    s2 = f"{an(discussion)} about {topic} may lead to {feeling}."
    s2 = sentence_case(s2)
    return f"{s1} {s2}"


def date_prediction_s(mood):
    days_in_future = random.randint(2, 8)
    significant_day = date.today() + timedelta(days=days_in_future)
    month = significant_day.strftime("%B")
    day = significant_day.strftime("%d").lstrip("0")

    r = random.random()

    if r <= 0.5:
        s = f"{month} {day} will be an important day for you"
    elif r <= 0.8:
        s = f"Interesting things await you on {month} {day}"
    else:
        s = f"The events of {month} {day} have the potential to change your life."

    return sentence_case(s)


def feeling_statement_s(mood):
    adjectives = wordlist("_feeling_adjs", prefix=mood)
    degrees = wordlist("neutral_degrees") + wordlist("_degrees", prefix=mood)

    adj = choose_from(adjectives)
    adj = ing_to_ed(adj)
    degree = choose_from(degrees)
    ending = positive_intensifier if mood == "good" else consolation
    exciting = mood == "good" and random.random() <= 0.5
    are = random.choice([" are", "'re"])
    s = f"You{are} feeling {degree} {adj}"
    s += ending()
    return sentence_case(s, exciting)


def positive_intensifier():
    r = random.random()

    if r <= 0.25:
        verb = random.choice(["say", "do"])
        return f", and there's nothing anyone can {verb} to stop you"
    elif r <= 0.95:
        return ", and you don't care who knows it"
    else:
        return ", and you don't give a fuck"


def consolation():
    r = random.random()

    if r <= 0.6:
        when = random.choice(["shortly", "soon", "in due time"])
        return f", but don't worry, everything will improve {when}"
    elif r <= 0.9:
        return ", perhaps you need a change in your life?"
    else:
        return "..."


def warning_s():
    r = random.random()
    avoid_list = wordlist("avoid_list")
    bad_thing = random.choice(avoid_list)

    if r <= 0.27:
        s = f"You would be well advised to avoid {bad_thing}"
    elif r <= 0.54:
        s = f"Avoid {bad_thing} at all costs"
    elif r <= 0.81:
        s = f"Steer clear of {bad_thing} for a stress-free week"
    else:
        also_bad = choose_uniq({bad_thing}, avoid_list)
        s = f"For a peaceful week, avoid {bad_thing} and {also_bad}"

    return sentence_case(s)


def cosmic_implication_s(mood):
    c_event = cosmic_event()
    prediction_verbs = wordlist("prediction_verbs")
    verb = choose_from(prediction_verbs)

    r = random.random()
    beginnings = wordlist("beginnings")
    endings = wordlist("endings")
    if mood == "bad" and r <= 0.5:
        junction = choose_from(beginnings)
        e_event = emotive_event("bad")
    elif mood == "bad":
        junction = choose_from(endings)
        e_event = emotive_event("good")
    elif mood == "good" and r <= 0.5:
        junction = choose_from(beginnings)
        e_event = emotive_event("good")
    else:
        junction = choose_from(endings)
        e_event = emotive_event("bad")

    s = f"{c_event} {verb} the {junction} of {e_event}"
    return sentence_case(s)


def cosmic_event():
    r = random.random()

    planets = wordlist("planets")
    stars = wordlist("stars")
    wanky_events = wordlist("wanky_events")
    aspects = wordlist("aspects")

    if r <= 0.25:
        return random.choice(planets) + " in retrograde"
    elif r <= 0.5:
        c_event = "the " + random.choice(["waxing", "waning"])
        c_event += " of " + choose_from(planets, ["the moon"], stars)
        return c_event
    elif r <= 0.6:
        return "the " + random.choice(["New", "Full"]) + " Moon"
    elif r <= 0.75:
        return random.choice(wanky_events)
    else:
        first = choose_from(planets, stars, ["Moon"])
        second = choose_uniq({first}, planets, stars, ["Moon"])
        return f"The {first}/{second} {choose_from(aspects)}"


def emotive_event(mood):
    feeling_adjs = wordlist("_feeling_adjs", prefix=mood)
    emotive_adjs = wordlist("_emotive_adjs", prefix=mood)
    feeling_nouns = wordlist("_feeling_nouns", prefix=mood)
    emotive_nouns = wordlist("_emotive_nouns", prefix=mood)
    time_periods = wordlist("time_periods")
    time_period = random.choice(time_periods)

    if random.random() <= 0.5:
        adj = choose_from(feeling_adjs, emotive_adjs)
        return f"{adj} {time_period}"
    else:
        noun = choose_from(feeling_nouns, emotive_nouns)
        return f"{time_period} of {noun}"


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        dc.log_command_usage("jyotish", update)

        horoscope = generate()

        logger.info("[jyotish] generated horoscope={}", horoscope)

        await update.message.reply_text(horoscope)

    except Exception as e:
        logger.error(
            "Caught Error in jyotish.handle - {} \n {}",
            e,
            traceback.format_exc(),
        )
