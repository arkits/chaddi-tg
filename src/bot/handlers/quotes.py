from loguru import logger
from peewee import DoesNotExist
from telegram import Update, ParseMode
from src.domain import dc, util, config
from src.db import Quote, quote as quote_dao
import random
import datetime
import traceback
import html

app_config = config.get_config()

MESSAGE_TRY_ADDING = (
    "Try adding a new Quotes by replying to any message with <code>/quotes add</code>"
)

MESSAGE_ADDED_QUOTE = "✏️ Rote memorization successful! You can retrive this Quote by posting <code>/quotes get {}</code>"


def handle(update: Update, context):

    try:

        dc.log_command_usage("quotes", update)

        # Extract query...
        query = update.message.text
        query = query.split(" ")

        command = None

        try:
            command = query[1].lower()
        except:
            command = "random"

        logger.debug("[quotes] command={}", command)

        if command == "add":
            if update.message.reply_to_message.text:
                q = quote_dao.add_quote_from_update(update)
                response = MESSAGE_ADDED_QUOTE.format(q.quote_id)
                update.message.reply_text(text=response, parse_mode=ParseMode.HTML)

        elif command == "remove":
            if util.is_admin_tg_user(update.message.from_user):
                try:
                    id_to_remove = query[2]
                except:
                    update.message.reply_text(
                        text="Please include the Quote ID you want to remove!",
                        parse_mode=ParseMode.HTML,
                    )
                    return

                response = Quote.delete_by_id(id_to_remove)

                if response == 1:
                    response = "Removed Quote - ID=<code>{}</code>".format(id_to_remove)
                else:
                    response = "Arrey isko hatao re..."

            else:
                response = "Chal kat re bsdk!"

            update.message.reply_text(text=response, parse_mode=ParseMode.HTML)

        elif command == "get":

            response = ""

            try:
                quote_id = query[2]
            except:
                update.message.reply_text(
                    text="Please include the Quote ID you want to get!",
                    parse_mode=ParseMode.HTML,
                )
                return

            try:

                quote = Quote.get_by_id(quote_id)

            except DoesNotExist:

                group_id = util.get_group_id_from_update(update)
                if group_id is None:
                    update.message.reply_text(text="Can't run this command here!")
                    return

                # Return a random quote
                quote = get_random_quote_from_group(group_id)

                if quote is None:
                    logger.info("[quotes] No quotes found! - group_id={}", group_id)
                    update.message.reply_text(
                        text="No quotes found for this Group! You can add quotes with `/quotes add`",
                        parse_mode=ParseMode.MARKDOWN,
                    )
                    return

                response = "Couldn't find quote with ID <code>{}</code>... but here's a random one -".format(
                    quote_id
                )

            pretty_quote = generate_pretty_quote(quote)
            response = response + pretty_quote
            update.message.reply_text(text=response, parse_mode=ParseMode.HTML)

        else:

            group_id = util.get_group_id_from_update(update)
            if group_id is None:
                update.message.reply_text(text="Can't run this command here!")
                return

            quote = get_random_quote_from_group(group_id)

            pretty_quote = generate_pretty_quote(quote)

            pretty_quote = pretty_quote + "\n" + MESSAGE_TRY_ADDING

            update.message.reply_text(text=pretty_quote, parse_mode=ParseMode.HTML)

    except Exception as e:
        logger.error(
            "Caught Error in quotes.handle - {} \n {}",
            e,
            traceback.format_exc(),
        )


def generate_pretty_quote(quote: Quote):

    if quote is None:
        return ""

    pretty_quote = """
<pre>
{}
</pre>
<b>~ by श्री {}</b>
<b>~ on {}</b>
<b>~ ID:</b> <code>{}</code>
        """.format(
        html.escape(quote.text),
        util.extract_pretty_name_from_bakchod(quote.author_bakchod),
        quote.created,
        quote.quote_id,
    )

    return pretty_quote


def get_random_quote_from_group(group_id: str) -> Quote:

    all_quotes_in_group = (
        Quote.select().where(Quote.quoted_in_group == group_id).execute()
    )

    all_quotes = []

    if len(all_quotes_in_group) > 0:

        for quote in all_quotes_in_group:
            all_quotes.append(quote)

        random.seed(datetime.datetime.now())

        random.shuffle(all_quotes)

        random_quote = random.choice(all_quotes)

        return random_quote

    else:

        return None
