from loguru import logger
from util import util, config
from db import dao
import json
import random
import datetime
import shortuuid
from telegram import ParseMode

chaddi_config = config.get_config()


def handle(update, context):

    util.log_chat("quotes", update)

    # Extract query...
    query = update.message.text
    query = query.lower()
    query = query.split(" ")

    command = None

    try:
        command = query[1]
    except:
        command = "random"

    if command == "add":
        if update.message.reply_to_message.text:
            response = add_quote(update)
            update.message.reply_text(text=response, parse_mode=ParseMode.MARKDOWN)

    elif command == "remove":
        if util.is_admin(update.message.from_user["id"]):
            try:
                id_to_remove = query[2]
            except:
                update.message.reply_text(
                    text="Please include the Quote ID you want to remove!",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return
            response = remove_quote(id_to_remove)
        else:
            response = "Chal kat re bsdk!"

        update.message.reply_text(text=response, parse_mode=ParseMode.MARKDOWN)

    elif command == "get":
        try:
            quote_id = query[2]
        except:
            update.message.reply_text(
                text="Please include the Quote ID you want to remove!",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        quote = get_quote_by_id(quote_id)

        pretty_quote = generate_pretty_quote(quote)

        update.message.reply_text(text=pretty_quote, parse_mode=ParseMode.MARKDOWN)

    else:
        # Return a random quote
        random_quote = get_random_quote()

        logger.info("[quotes] Got a random quote '{}", random_quote)

        pretty_quote = generate_pretty_quote(random_quote)

        update.message.reply_text(text=pretty_quote, parse_mode=ParseMode.MARKDOWN)


def generate_pretty_quote(quote):

    pretty_quote = """
```
{}
```
*~ by श्री {}*
*~ on {}*
~ ID: `{}`
    """.format(
        str(quote["message"]), str(quote["user"]), str(quote["date"]), str(quote["id"])
    )

    return pretty_quote


# Add the quoted message to quotes_dict
def add_quote(update):

    quote_id = shortuuid.uuid()

    quoted_message = update.message.reply_to_message.text
    quoted_message = quoted_message.encode(encoding="UTF-8")

    if update.message.reply_to_message.from_user["username"]:
        quoted_user = update.message.reply_to_message.from_user["username"]
        quoted_user = "@" + quoted_user
    else:
        quoted_user = update.message.reply_to_message.from_user["first_name"]

    quoted_date = update.message.reply_to_message.date

    quote = {
        "message": quoted_message,
        "user": quoted_user,
        "date": quoted_date,
        "id": quote_id,
    }

    dao.insert_quote(quote)

    logger.info(
        "[quotes] Added Quoted Message to quotes_dict[{}] - {}",
        quote_id,
        quoted_message,
    )

    response = "✏️ Rote memorization successful! ({})".format(quote_id)

    return response


# Returns a random quote
def get_random_quote():

    all_quotes_ids = dao.get_all_quotes_ids()

    random.seed(datetime.datetime.now())
    random_quote_id = random.choice(all_quotes_ids)

    random_quote = dao.get_quote_by_id(random_quote_id)

    return random_quote


# Removes quote based on it's ID
def remove_quote(id_to_remove):

    try:
        dao.delete_quote_by_id(id_to_remove)
        response = "Removing Quote!"

    except:
        response = "Unable to remove quote :("

    return response


# Returns a quote by ID
def get_quote_by_id(quote_id):

    quote_to_return = None

    try:
        quote_to_return = dao.get_quote_by_id(quote_id)
    except Exception as e:
        pass

    return quote_to_return
