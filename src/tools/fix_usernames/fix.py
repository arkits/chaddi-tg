from loguru import logger
from db import dao
from models.bakchod import Bakchod


def main():
    logger.info("Hiiii")

    bakchods = dao.get_all_bakchods()

    for bakchod in bakchods:

        username = bakchod.username

        if username is not None:
            if username[0] == "@":
                logger.info("Fixing - {}", username[1:])
                bakchod.username = username[1:]
                dao.insert_bakchod(bakchod)


if __name__ == "__main__":
    main()
