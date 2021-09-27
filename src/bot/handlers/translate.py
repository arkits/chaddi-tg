from loguru import logger
from telegram import Update, ParseMode
from src.domain import dc
import traceback
from googletrans import Translator

translator = Translator()


def handle(update: Update, context):

    try:

        dc.log_command_usage("translate", update)

        if update.message.reply_to_message is None:
            logger.debug(
                "[translate] user didn't reply to another user",
            )
            update.message.reply_text(
                "Try replying to a message with `/translate` to translate it to English",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        # Extract target language from command params
        target_language = None

        params = update.message.text.split(" ")
        if len(params) > 1:
            target_language = params[1]

        if target_language is None:
            target_language = "en"

        # Extract text_to_translate from various possible sources
        text_to_translate = None
        if update.message.reply_to_message.text:
            text_to_translate = update.message.reply_to_message.text
        elif update.message.reply_to_message.caption:
            text_to_translate = update.message.reply_to_message.caption

        if text_to_translate is None:
            logger.warning(
                "[translate] Failed to extract text to translate text_to_translate={}",
                text_to_translate,
            )
            update.message.reply_text(
                "Failed to extract text to translate :(",
                parse_mode=ParseMode.MARKDOWN,
            )
            return
        else:
            logger.debug(
                "[translate] text_to_translate={} target_language={}",
                text_to_translate,
                target_language,
            )

        try:
            translated = translator.translate(
                text=text_to_translate, dest=target_language
            )
            logger.info("[translate] translated={}", translated)

            reply_text = """
{}

```
Translated from {} to {}
```
""".format(
                translated.text, translated.src.upper(), translated.dest.upper()
            )

            update.message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:

            logger.error(
                "[translate] Caught error in googletrans text_to_translate={} e={}",
                text_to_translate,
                traceback.format_exc(),
            )

            update.message.reply_text(
                "Failed to translate :( googletrans error={}".format(e),
                parse_mode=ParseMode.MARKDOWN,
            )

    except Exception as e:

        logger.error(
            "Caught Error in translate.handle - {} \n {}",
            e,
            traceback.format_exc(),
        )
        return
