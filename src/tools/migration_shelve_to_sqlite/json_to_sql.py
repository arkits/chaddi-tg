import json
from db import dao
from loguru import logger
from models.bakchod import Bakchod
from models.group import Group


def main():

    logger.info("Test")


    # f = open("quotes.json", "r")
    # quotes = f.read()
    # quotes = json.loads(quotes) 
    # for quote in quotes.values():
    #     logger.info(quote)
    #     dao.insert_quote(quote)

    # f = open("bakchods.json", "r")
    # quotes = f.read()
    # quotes = json.loads(quotes)
    # for quote in quotes:
    #     logger.info(quote)
    #     bakchod = Bakchod(quote["id"], None, None)
    #     bakchod.username = quote.get("username")
    #     bakchod.first_name = quote.get("first_name")
    #     bakchod.lastseen = quote.get("lastseen")
    #     bakchod.rokda = quote.get("rokda")
    #     bakchod.censored = quote.get("censored")
    #     bakchod.history = quote.get("history")
    #     dao.insert_bakchod(bakchod)

    f = open("groups.json", "r")
    quotes = f.read()
    quotes = json.loads(quotes)
    for quote in quotes:
        logger.info(quote)
        group = Group(None, None)
        group.id = quote.get("id")
        group.title = quote.get("title")
        group.members = quote.get("members")
        dao.insert_group(group)


if __name__ == "__main__":
    main()
