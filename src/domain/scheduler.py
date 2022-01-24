import json
import time
from loguru import logger
from src.db import ScheduledJob

from src.bot.handlers.remind import reminder_handler, build_job_name


def reschedule_saved_jobs(job_queue):

    sjs = ScheduledJob.select()

    for sj in sjs:

        due_seconds = sj.job_context["reminder_time"] - int(time.time())

        job_name = build_job_name(
            sj.job_context["chat_id"],
            sj.job_context["from_bakchod_id"],
            sj.job_context["job_id"],
        )

        job_queue.run_once(
            reminder_handler,
            due_seconds,
            context=json.dumps(sj.job_context),
            name=job_name,
        )

        logger.info("Re-scheduled job_name={} job_context={}", job_name, sj.job_context)

    return
