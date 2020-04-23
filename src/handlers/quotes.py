from loguru import logger
from util import util, config
from db import dao
import json
import random
import datetime
import shortuuid
from telegram import ParseMode
import traceback

chaddi_config = config.get_config()


def handle(update, context):

    util.log_chat("quotes", update)

    try:

        # Extract query...
        query = update.message.text
        query = query.split(" ")

        command = None

        try:
            command = query[1].lower()
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

            response = ""

            try:
                quote_id = query[2]
            except:
                update.message.reply_text(
                    text="Please include the Quote ID you want to remove!",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return

            quote = get_quote_by_id(quote_id)

            if quote is None:
                quote = get_random_quote()
                response = "Couldn't find quote with ID `{}`... but here's a random one - \n".format(
                    quote_id
                )

            pretty_quote = generate_pretty_quote(quote)

            response = response + pretty_quote

            update.message.reply_text(text=response, parse_mode=ParseMode.MARKDOWN)

        elif command == "join":

            response = ""

            try:
                quote_id = query[2]
            except:
                update.message.reply_text(
                    text="Please include the Quote ID you want to join!",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return

            quote = get_quote_by_id(quote_id)

            if quote is None:
                update.message.reply_text(
                    text="Couldn't find quote with ID `{}`!".format(quote_id),
                    parse_mode=ParseMode.MARKDOWN,
                )
                return

            response = join_quotes(quote, update)

            update.message.reply_text(text=response, parse_mode=ParseMode.MARKDOWN)

        else:
            # Return a random quote
            random_quote = get_random_quote()

            logger.info("[quotes] Got a random quote '{}", random_quote)

            pretty_quote = generate_pretty_quote(random_quote)

            update.message.reply_text(text=pretty_quote, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(
            "Caught Error in quotes.handle - {} \n {}", e, traceback.format_exc(),
        )


def generate_pretty_quote(quote):

    pretty_quote = ""

    messages = quote["message"]

    for message in messages:
        pretty_quote = pretty_quote + "`{} <{}> {}` \n".format(
            str(message["date"]),
            str(message["user"]),
            sanitize_quote_message(message["message"]),
        )

    pretty_quote = pretty_quote + "\n ~ ID: `{}`".format(str(quote["id"]))

    return pretty_quote


# Add the quoted message to quotes_dict
def add_quote(update):

    try:
        quote_id = shortuuid.uuid()

        message = generate_message(update)

        quote = {
            "message": [message],
            "user": message["user"],
            "date": message["date"],
            "id": quote_id,
        }

        dao.insert_quote(quote)

        logger.info("[quotes] Added Quoted Message! - {}", quote)

        response = "✏️ Rote memorization successful! (`{}`)".format(quote_id)

    except Exception as e:
        logger.error(
            "Caught Error in quotes.add_quote - {} \n {}", e, traceback.format_exc(),
        )

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
        logger.error(
            "Caught Error in quotes.get_quote_by_id - {} \n {}",
            e,
            traceback.format_exc(),
        )

    return quote_to_return


def sanitize_quote_message(message):

    if isinstance(message, (bytes, bytearray)):
        return str(message, "utf-8")
    else:
        if message.startswith("b'"):
            trimed = message[2:-1]
            return trimed

    return message


def join_quotes(parent_quote, update):

    try:

        message = generate_message(update)

        parent_message = parent_quote["message"]
        parent_message.append(message)
        parent_quote["message"] = parent_message

        dao.insert_quote(parent_quote)

        response = "✏️ Quotes joined!"

    except Exception as e:
        logger.error(
            "Caught Error in quotes.join_quotes - {} \n {}", e, traceback.format_exc(),
        )

    return response


def generate_message(update):

    message = None

    try:

        quoted_message = update.message.reply_to_message.text
        quoted_message = quoted_message.encode(encoding="UTF-8")

        quoted_user = None

        if update.message.reply_to_message.forward_sender_name is not None:
            quoted_user = update.message.reply_to_message.forward_sender_name
        elif update.message.reply_to_message.forward_from is not None:
            quoted_user = util.extract_pretty_name_from_tg_user(update.message.reply_to_message.forward_from)
        else:
            quoted_user = util.extract_pretty_name_from_tg_user(
                update.message.reply_to_message.from_user
            )

        quoted_date = update.message.reply_to_message.date

        message = {"message": quoted_message, "user": quoted_user, "date": quoted_date}

    except Exception as e:
        logger.error(
            "Caught Error in quotes.generate_message - {} \n {}", e, traceback.format_exc(),
        )

    return message