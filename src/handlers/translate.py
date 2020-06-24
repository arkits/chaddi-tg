from loguru import logger
from util import util
import traceback
from googletrans import Translator
import telegram

translator = Translator()


def handle(update, context):

    try:

        util.log_chat("translate", update)

        if update.message.reply_to_message:
            text_to_translate = update.message.reply_to_message.text
        else:
            update.message.reply_text("Reply to the message you want to translate!")
            return

        if len(text_to_translate) > 2000:
            logger.debug(
                "[translate] text_to_translate is too long ({})... trimming to 2000!",
                len(text_to_translate),
            )
            text_to_translate = text_to_translate[:2000]

        if util.ratelimit_user(
            update, "translate", "Translator off-duty... come back later!", 2
        ):
            return

        result = translator.translate(text_to_translate)
        if result.text is None:
            return

        response = "<b>Translated from {} to {}:</b> \n <code>{}</code>".format(
            result.src.upper(), result.dest.upper(), result.text
        )

        logger.info("[translate] completed translation! response={}", response)

        update.message.reply_text(text=response, parse_mode=telegram.ParseMode.HTML)

    except Exception as e:
        logger.error(
            "Caught Error in translate.handle - {} \n {}", e, traceback.format_exc(),
        )
