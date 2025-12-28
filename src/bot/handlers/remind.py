import json
import random
import time
from datetime import datetime

from loguru import logger
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.db import Bakchod, ScheduledJob, scheduledjob_dao
from src.domain import dc, util


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        # check if user can create reminder
        reminders_created = scheduledjob_dao.get_scheduledjobs_by_bakchod(from_bakchod_id)
        if len(reminders_created) > 10:
            await update.message.reply_text(
                text="You have created too many reminders! Please cancel your previous ones, or wait for them to complete.",
                parse_mode=ParseMode.HTML,
            )
            return

        # parse the due_seconds
        due_seconds = parse_reminder_due(context.args)
        if due_seconds <= 0:
            await update.message.reply_text(
                text='<b>Usage:</b> <code>/remind 5m "Chai break"</code>',
                parse_mode=ParseMode.HTML,
            )
            return

        # validate due_seconds
        if due_seconds >= (10 * 365 * 86400):
            sticker_to_send = "CAADAQADrAEAAp6M4Ahtgp9JaiLJPxYE"
            await update.message.reply_sticker(sticker=sticker_to_send)
            return

        reminder_time = int(time.time()) + due_seconds

        # parse reminder_message
        reminder_message = extract_reminder_message(update.message.text)

        # build the job_context
        job_context = {
            "chat_id": chat_id,
            "due_seconds": due_seconds,
            "from_bakchod_id": from_bakchod_id,
            "reply_to_message_id": reply_to_message_id,
            "reminder_message": reminder_message,
            "reminder_time": reminder_time,
        }

        from_bakchod = Bakchod.get_by_id(from_bakchod_id)

        sj = ScheduledJob.create(
            created=datetime.now(),
            updated=datetime.now(),
            from_bakchod=from_bakchod,
            group=chat_id,
            job_context=job_context,
        )

        # build the job_name
        job_name = build_job_name(str(chat_id), str(from_bakchod_id), sj.job_id)

        # update job_context with new params
        job_context["job_id"] = sj.job_id
        job_context["job_name"] = job_name
        sj.job_context = job_context
        sj.save()

        # add to the job_queue
        context.job_queue.run_once(
            reminder_handler,
            due_seconds,
            data=json.dumps(job_context),
            name=job_name,
        )

        logger.info(
            "[remind] Scheduled Job job_name={} job_context={}",
            job_name,
            job_context,
        )

        await update.message.reply_text(
            f"""
<b>✅ Reminder set!</b>

I will reply to you in {util.pretty_time_delta(due_seconds)} as a reminder.

<b>Reminder ID:</b> {sj.job_id}
""",
            parse_mode=ParseMode.HTML,
        )

    except (IndexError, ValueError):
        await update.message.reply_text(
            text='<b>Usage:</b> </pre>/remind 5m "Chai break"</pre>',
            parse_mode=ParseMode.HTML,
        )


def build_job_name(chat_id, from_bakchod_id, job_id):
    return f"reminder/{chat_id!s}/{from_bakchod_id!s}/{job_id!s}"


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
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


async def reminder_handler(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        # extract job_context
        job = context.job
        job_context = json.loads(job.data)

        logger.debug("[reminder_handler] job={} job_context={}", job.__dict__, job_context)

        # build reply_text
        reply_text = f"""
{random.choice(REMINDER_RESPONSE_GREETINGS)}
"""

        # handle reminder_message
        if job_context["reminder_message"] != "":
            reply_text = (
                reply_text
                + """
<b>> {}</b>
""".format(job_context["reminder_message"])
            )

        # send the message
        await context.bot.send_message(
            chat_id=job_context["chat_id"],
            text=reply_text,
            reply_to_message_id=job_context["reply_to_message_id"],
            parse_mode=ParseMode.HTML,
        )

        # delete from db
        ScheduledJob.delete_by_id(job_context["job_id"])

    except Exception as e:
        logger.error("Caught exception in reminder_handler e={}", e)


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
            logger.trace(f"digit={digit} value_indicator={value_indicator}")

            if value_indicator == "min" or value_indicator == "mins" or value_indicator == "m":
                digit = digit * 60

            if (
                value_indicator == "hour"
                or value_indicator == "hours"
                or value_indicator == "hr"
                or value_indicator == "hrs"
                or value_indicator == "h"
            ):
                digit = digit * 60 * 60

            if value_indicator == "day" or value_indicator == "days" or value_indicator == "d":
                digit = digit * 24 * 60 * 60

            due_seconds = due_seconds + digit

        else:
            logger.trace(f"Not digit... continuing - a={a}")
            continue

    return due_seconds


def extract_reminder_message(message: str):
    custom_message = ""
    s = message.split('"')
    if len(s) >= 2:
        custom_message = "".join(s[1:])
    return custom_message
