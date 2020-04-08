import json
import shelve
from loguru import logger
import traceback

def main():

    json_bakchods = []

    try:
        with shelve.open("resources/db/groups", "r") as shelf:
            bakchods = shelf.get("groups")

            for b in bakchods.values():
                json_bakchod = b.__dict__
                json_bakchods.append(json_bakchod)

            json_bakchods = json.dumps(json_bakchods, indent=4, sort_keys=True, default=str)

            logger.info(json_bakchods)
            f = open("groups.json", "w")
            f.write(str(json_bakchods))
            f.close()

            shelf.close()
    except Exception as e:
        logger.error(
            "Caught Error in dao.get_bakchod - {} \n {}", e, traceback.format_exc()
        )


if __name__ == "__main__":
    main()
