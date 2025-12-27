import datetime
import json
import random
import time

import peewee
import pytz
from loguru import logger
from telegram.ext import ContextTypes, JobQueue

from src.bot.handlers.remind import build_job_name, reminder_handler
from src.db import Group, Quote, ScheduledJob


def reschedule_saved_jobs(job_queue: JobQueue):
    sjs = ScheduledJob.select()
    current_time = int(time.time())
    rescheduled_count = 0
    skipped_count = 0

    for sj in sjs:
        due_seconds = sj.job_context["reminder_time"] - current_time

        # Skip jobs that are in the past
        if due_seconds <= 0:
            job_name = build_job_name(
                sj.job_context["chat_id"],
                sj.job_context["from_bakchod_id"],
                sj.job_context["job_id"],
            )
            logger.warning(
                "Skipping past job job_name={} due_seconds={} (was scheduled for the past)",
                job_name,
                due_seconds,
            )
            # Delete the old job from database
            sj.delete_instance()
            skipped_count += 1
            continue

        job_name = build_job_name(
            sj.job_context["chat_id"],
            sj.job_context["from_bakchod_id"],
            sj.job_context["job_id"],
        )

        job_queue.run_once(
            reminder_handler,
            due_seconds,
            data=json.dumps(sj.job_context),
            name=job_name,
        )

        logger.info("Re-scheduled job_name={} job_context={}", job_name, sj.job_context)
        rescheduled_count += 1

    logger.info(
        "Job rescheduling complete: rescheduled={} skipped={}",
        rescheduled_count,
        skipped_count,
    )

    return


async def daily_post_callback(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Running daily post job")

    groups = Group.select()
    enabled_groups = [
        g for g in groups if g.metadata and g.metadata.get("good_morning_enabled")
    ]

    if not enabled_groups:
        logger.info("No groups have good morning enabled")
        return

    greetings = [
        "Good morning!",
        "Rise and shine!",
        "Top of the morning to you!",
        "Wakey wakey, eggs and bakey!",
        "Good morning, sunshine!",
        "Subah ho gayi mamu!",
    ]

    for group in enabled_groups:
        greeting = random.choice(greetings)

        # Get a random quote from this group
        quote = (
            Quote.select()
            .where(Quote.quoted_in_group == group)
            .order_by(peewee.fn.Random())
            .limit(1)
            .first()
        )

        message_text = f"🌅 {greeting}\n\n"
        if quote:
            author_name = (
                quote.author_bakchod.pretty_name
                or quote.author_bakchod.username
                or "Unknown"
            )
            message_text += f"💡 *Daily Quote:*\n_{quote.text}_\n- {author_name}"

        try:
            await context.bot.send_message(
                chat_id=group.group_id, text=message_text, parse_mode="Markdown"
            )
            logger.info(f"Sent daily post to group {group.name} ({group.group_id})")
        except Exception as e:
            logger.error(f"Failed to send daily post to group {group.name}: {e}")


def schedule_daily_posts(job_queue: JobQueue):
    # IST is UTC+5:30
    ist = pytz.timezone("Asia/Kolkata")
    # Schedule for 8:00 AM IST
    daily_time = datetime.time(hour=8, minute=0, tzinfo=ist)

    job_queue.run_daily(daily_post_callback, time=daily_time, name="daily_good_morning")
    logger.info("Scheduled daily good morning job for 8:00 AM IST")
