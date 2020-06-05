from loguru import logger
from util import util
from datetime import time
import handlers
import pytz

# Indian Standard Timezone
ist = pytz.timezone("Asia/Kolkata")


def schedule_timer_jobs(job_queue):

    logger.info("Scheduling timer jobs...")

    # Run good_morning job once 1 sec after startup... for debugging
    # job_queue.run_once(handlers.good_morning.handle, 1)

    ten_am = time(hour=10, minute=00, tzinfo=ist)
    job_queue.run_daily(handlers.year.handle, ten_am)

    eleven_am = time(hour=11, minute=00, tzinfo=ist)
    job_queue.run_daily(handlers.roll.start_new_daily_roll, eleven_am)

    nine_pm = time(hour=21, minute=00, tzinfo=ist)
    job_queue.run_daily(handlers.roll.start_new_daily_roll, nine_pm)
