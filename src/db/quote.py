import datetime

import shortuuid
from loguru import logger
from telegram import Update

from src.db import Quote, bakchod_dao, group_dao
from src.domain import metrics, util


def add_quote_from_update(update: Update) -> Quote:
    quoted_message = update.message.reply_to_message

    # Check if message is forwarded (handle both old and new API versions)
    forward_from = getattr(quoted_message, "forward_from", None)

    if forward_from:
        # if the message is a forwarded message, then use the original author
        author_bakchod = bakchod_dao.get_or_create_bakchod_from_tg_user(forward_from)
    else:
        # otherwise, use the author of the message
        author_bakchod = bakchod_dao.get_or_create_bakchod_from_tg_user(quoted_message.from_user)

    quote_capture_bakchod = bakchod_dao.get_or_create_bakchod_from_tg_user(update.message.from_user)

    quoted_in_group = group_dao.get_or_create_group_from_chat(quoted_message.chat)

    q = Quote.create(
        quote_id=shortuuid.uuid(),
        message_id=quoted_message.message_id,
        created=datetime.datetime.now(),
        author_bakchod=author_bakchod,
        quote_capture_bakchod=quote_capture_bakchod,
        quoted_in_group=quoted_in_group,
        text=quoted_message.text,
        update=update.to_dict(),
    )

    logger.debug(
        "[db] saved Quote - id={} author_bakchod={} quote_capture_bakchod={}",
        q.message_id,
        util.extract_pretty_name_from_bakchod(author_bakchod),
        util.extract_pretty_name_from_bakchod(quote_capture_bakchod),
    )

    metrics.inc_message_count(update)

    return q
