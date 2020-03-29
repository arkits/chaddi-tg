from loguru import logger
from util import dao
from models.bakchod import Bakchod
from domain import bakchod as bakchod_domain
import time
import datetime


def all(update, context):

    bakchod = dao.get_bakchod(update.message.from_user.id)

    if bakchod is None:
        bakchod = Bakchod.fromUpdate(update)
        logger.info("Looks like we have a new Bakchod! - {}", bakchod.__dict__)

    update_bakchod(bakchod)


def update_bakchod(bakchod):

    # Update rokda
    bakchod.rokda = bakchod_domain.reward_rokda(bakchod.rokda)

    # Update lastseen
    bakchod.lastseen = datetime.datetime.now()

    # Persist updated Bakchod
    dao.update_bakchod(bakchod)
