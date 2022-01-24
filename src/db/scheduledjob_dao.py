from peewee import DoesNotExist
from loguru import logger
from src.db import Bakchod, Roll, ScheduledJob


def get_scheduledjobs_by_bakchod(bakchod_id: str) -> Roll:

    try:

        b = Bakchod.get_by_id(bakchod_id)

        sjs = (
            ScheduledJob.select()
                .where(ScheduledJob.from_bakchod == b)
                .execute()
        )

        jobs = []
        
        for sj in sjs:
            jobs.append(sj)

        return jobs

    except DoesNotExist:

        return None