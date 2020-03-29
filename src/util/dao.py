from loguru import logger
import json
import shelve
import traceback

db_list = ["bakchods", "groups", "quotes"]


def init_db():

    logger.info("Initializing DBs...")

    for db in db_list:

        try:
            with shelve.open("resources/db/" + db, "c") as shelf:

                if shelf.get(db) is not None:
                    logger.debug("db={} is already setup...", db)
                else:
                    logger.debug("Setting up db={}", db)
                    shelf[db] = {}

                shelf.close()
        except Exception as e:
            logger.error(
                "Caught Error in dao.init_db - {} \n {}", e, traceback.format_exc()
            )

    return


def update_bakchod(bakchod):

    try:
        with shelve.open("resources/db/bakchods", "c") as shelf:
            bakchods = shelf["bakchods"]
            bakchods[bakchod.id] = bakchod
            shelf["bakchods"] = bakchods
            shelf.close()
    except Exception as e:
        logger.error(
            "Caught Error in dao.get_bakchod - {} \n {}", e, traceback.format_exc()
        )

    return


def get_bakchod(bakchod_id):

    bakchod_to_return = None

    try:
        with shelve.open("resources/db/bakchods", "r") as shelf:
            bakchods = shelf.get("bakchods")
            bakchod_to_return = bakchods.get(bakchod_id)
            shelf.close()
    except Exception as e:
        logger.error(
            "Caught Error in dao.get_bakchod - {} \n {}", e, traceback.format_exc()
        )

    return bakchod_to_return


def update_group(group):

    try:
        with shelve.open("resources/db/groups", "c") as shelf:
            groups = shelf["groups"]
            groups[group.id] = group
            shelf["groups"] = groups
            shelf.close()
    except Exception as e:
        logger.error(
            "Caught Error in dao.update_group - {} \n {}", e, traceback.format_exc()
        )

    return


def get_group(group_id):

    group_to_return = None

    try:
        with shelve.open("resources/db/groups", "r") as shelf:
            groups = shelf.get("groups")
            group_to_return = groups.get(group_id)
            shelf.close()
    except Exception as e:
        logger.error(
            "Caught Error in dao.get_group - {} \n {}", e, traceback.format_exc()
        )

    return group_to_return


# Initialize DBs on startup
init_db()
