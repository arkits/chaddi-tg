import json
from loguru import logger
from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from src.domain import dc, util
import random


def handle(update: Update, context: CallbackContext):

    dc.log_command_usage("remind", update)

    chat_id = update.message.chat_id
    from_bakchod_id = update.message.from_user["id"]

    if update.message.reply_to_message is None:
        # user didn't reply to any message
        reply_to_message_id = update.message.message_id
    else:
        # user replied to a message... use the original message as the reply target
        reply_to_message_id = update.message.reply_to_message.message_id

    try:

        due_seconds = parse_reminder_due(context.args)
        if due_seconds <= 0:
            update.message.reply_text(
                text="<b>Usage:</b> <code>/remind 5m \"Chai break\"</code>", 
                parse_mode=ParseMode.HTML
            )
            return

        if due_seconds >= (31*86400):
            sticker_to_send = "CAADAQADrAEAAp6M4Ahtgp9JaiLJPxYE"
            update.message.reply_sticker(sticker=sticker_to_send)
            return

        reminder_message = extract_reminder_message(update.message.text)

        job_context = {
            "chat_id": chat_id,
            "due_seconds": due_seconds,
            "from_bakchod_id": from_bakchod_id,
            "reply_to_message_id": reply_to_message_id,
            "reminder_message": reminder_message   
        }
        job_context = json.dumps(job_context)

        job_name = build_job_name(str(chat_id), str(from_bakchod_id))

        logger.info(
            "[remind] Scheduling reminder job_name={} job_context={}",
            job_name,
            job_context,
        )
        context.job_queue.run_once(
            reminder_handler, due_seconds, context=job_context, name=job_name
        )

        update.message.reply_text(
            """
<b>✅ Reminder set!</b>

I will reply to you in {} as a reminder.
""".format(
                util.pretty_time_delta(due_seconds)
            ),
            parse_mode=ParseMode.HTML,
        )

    except (IndexError, ValueError):
        update.message.reply_text(
            text="<b>Usage:</b> </pre>/remind 5m \"Chai break\"</pre>", 
            parse_mode=ParseMode.HTML
        )


def build_job_name(chat_id, from_bakchod_id):
    return "reminder/{}/{}".format(str(chat_id), str(from_bakchod_id))


def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


REMINDER_RESPONSE_GREETINGS = [
    "REMINDER!",
    "TIME IS UP!",
    "HELLLOOOO!",
    "NAMASKAR MANDALI!",
]


def reminder_handler(context: CallbackContext) -> None:
    job = context.job
    job_context = json.loads(job.context)

    logger.debug("[reminder_handler] job={} job_context={}", job.__dict__, job_context)

    reply_text = """
{}
""".format(
        random.choice(REMINDER_RESPONSE_GREETINGS),
    )

    if job_context["reminder_message"] != "":
        reply_text = reply_text + """
<b>> {}</b>
""".format(job_context["reminder_message"])

    context.bot.send_message(
        chat_id=job_context["chat_id"],
        text=reply_text,
        reply_to_message_id=job_context["reply_to_message_id"],
        parse_mode=ParseMode.HTML
    )


def parse_reminder_due(args):

    due_seconds = 0
    for idx, a in enumerate(args):

        if a[0].isdigit():

            digit = ""
            value_indicator = ""

            if a.isdigit():
                digit = int(a)
                try:
                    value_indicator = args[idx + 1]
                except IndexError:
                    logger.trace("Caught IndexError, defaulting value_indicator to seconds")
            else:
                # handle case where digit and value indicator are together
                for char in a:
                    if char.isdigit():
                        digit = digit + char
                    else:
                        value_indicator = value_indicator + char

                digit = int(digit)

            value_indicator = value_indicator.lower()
            logger.trace("digit={} value_indicator={}".format(
                digit, value_indicator))

            if value_indicator == "min" or value_indicator == "m" or value_indicator == "mins":
                digit = digit * 60

            if value_indicator == "hour" or value_indicator == "hr" or value_indicator == "h":
                digit = digit * 60 * 60

            if value_indicator == "day" or value_indicator == "d" or value_indicator == "days":
                digit = digit * 60 * 60 * 60

            due_seconds = due_seconds + digit

        else:
            logger.trace("Not digit... continuing - a={}".format(a))
            continue

    return due_seconds


def extract_reminder_message(message: str):
    custom_message = ""
    s = message.split("\"")
    if len(s) >= 2:
        custom_message = "".join(s[1:])
    return custom_message