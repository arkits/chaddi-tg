import json
import time

from loguru import logger

from src.bot.handlers.remind import build_job_name, reminder_handler
from src.db import ScheduledJob


def reschedule_saved_jobs(job_queue):
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
