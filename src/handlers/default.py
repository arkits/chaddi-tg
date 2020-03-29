from loguru import logger
from util import dao
from models.bakchod import Bakchod
from models.group import Group
from domain import bakchod as bakchod_domain
import time
import datetime


def all(update, context):

    bakchod = dao.get_bakchod(update.message.from_user.id)

    if bakchod is None:
        bakchod = Bakchod.fromUpdate(update)
        logger.info("Looks like we have a new Bakchod! - {}", bakchod.__dict__)

    bakchod = update_bakchod(bakchod, update)

    group = dao.get_group(update.message.chat.id)

    if group is None:
        group = Group.fromUpdate(update)
        logger.info("Looks like we have a new Group! - {}", group.__dict__)

    update_group(group, bakchod)

    logger.info(group.__dict__)


def update_bakchod(bakchod, update):

    # usernames and first_name are mutable... have to keep them in sync
    bakchod.username = update.message.from_user.username
    bakchod.first_name = update.message.from_user.first_name

    # Update rokda
    bakchod.rokda = bakchod_domain.reward_rokda(bakchod.rokda)

    # Update lastseen
    bakchod.lastseen = datetime.datetime.now()

    # Persist updated Bakchod
    dao.update_bakchod(bakchod)

    return bakchod


def update_group(group, bakchod):

    # Add Bakchod to Group
    if bakchod.id not in group.members:
        group.members.append(bakchod.id)

    # Persist updated Group
    dao.update_group(group)
