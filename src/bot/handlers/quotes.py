import datetime
import html
import random
import traceback

from loguru import logger
from peewee import DoesNotExist
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.db import Quote
from src.db import quote as quote_dao
from src.domain import config, dc, util

app_config = config.get_config()

MESSAGE_TRY_ADDING = (
    "Try adding a new Quotes by replying to any message with <code>/quotes add</code>"
)

MESSAGE_ADDED_QUOTE = "✏️ Rote memorization successful! You can retrive this Quote by posting <code>/quotes get {}</code>"


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        dc.log_command_usage("quotes", update)

        # Extract query...
        query = update.message.text
        query = query.split(" ")

        command = None

        try:
            command = query[1].lower()
        except Exception:
            # No second token -> default to random
            command = "random"

        logger.debug("[quotes] command={}", command)

        if command == "add":
            # Ensure the command is used as a reply with text
            if getattr(update.message, "reply_to_message", None) and getattr(
                update.message.reply_to_message, "text", None
            ):
                q = quote_dao.add_quote_from_update(update)
                response = MESSAGE_ADDED_QUOTE.format(q.quote_id)
                await update.message.reply_text(text=response, parse_mode=ParseMode.HTML)

        elif command == "remove":
            if util.is_admin_tg_user(update.message.from_user):
                try:
                    id_to_remove = query[2]
                except Exception:
                    await update.message.reply_text(
                        text="Please include the Quote ID you want to remove!",
                        parse_mode=ParseMode.HTML,
                    )
                    return

                response = Quote.delete_by_id(id_to_remove)

                if response == 1:
                    response = f"Removed Quote - ID=<code>{id_to_remove}</code>"
                else:
                    response = "Arrey isko hatao re..."

            else:
                response = "Chal kat re bsdk!"

            await update.message.reply_text(text=response, parse_mode=ParseMode.HTML)

        elif command == "get":
            response = ""

            try:
                quote_id = query[2]
            except Exception:
                await update.message.reply_text(
                    text="Please include the Quote ID you want to get!",
                    parse_mode=ParseMode.HTML,
                )
                return

            try:
                quote = Quote.get_by_id(quote_id)

            except DoesNotExist:
                group_id = util.get_group_id_from_update(update)
                if group_id is None:
                    await update.message.reply_text(text="Can't run this command here!")
                    return

                # Return a random quote
                quote = get_random_quote_from_group(group_id)

                if quote is None:
                    logger.info("[quotes] No quotes found! - group_id={}", group_id)
                    await update.message.reply_text(
                        text="No quotes found for this Group! You can add quotes with `/quotes add`",
                        parse_mode=ParseMode.MARKDOWN,
                    )
                    return

                response = f"Couldn't find quote with ID <code>{quote_id}</code>... but here's a random one -"

            pretty_quote = generate_pretty_quote(quote)
            response = response + pretty_quote
            await update.message.reply_text(text=response, parse_mode=ParseMode.HTML)

        else:
            group_id = util.get_group_id_from_update(update)
            if group_id is None:
                await update.message.reply_text(text="Can't run this command here!")
                return

            quote = get_random_quote_from_group(group_id)

            pretty_quote = generate_pretty_quote(quote)

            pretty_quote = pretty_quote + "\n" + MESSAGE_TRY_ADDING

            await update.message.reply_text(text=pretty_quote, parse_mode=ParseMode.HTML)

    except Exception as e:
        logger.error(
            "Caught Error in quotes.handle - {} \n {}",
            e,
            traceback.format_exc(),
        )


def generate_pretty_quote(quote: Quote):
    if quote is None:
        return ""

    pretty_quote = f"""
<pre>
{html.escape(quote.text)}
</pre>
<b>~ by श्री {util.extract_pretty_name_from_bakchod(quote.author_bakchod)}</b>
<b>~ on {quote.created}</b>
<b>~ ID:</b> <code>{quote.quote_id}</code>
        """

    return pretty_quote


def get_random_quote_from_group(group_id: str) -> Quote:
    all_quotes_in_group = Quote.select().where(Quote.quoted_in_group == group_id).execute()

    all_quotes = []

    if len(all_quotes_in_group) > 0:
        for quote in all_quotes_in_group:
            all_quotes.append(quote)

        random.shuffle(all_quotes)

        random_quote = random.choice(all_quotes)

        return random_quote

    else:
        return None
