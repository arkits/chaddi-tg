from loguru import logger
from db import dao


def main():
    logger.info("Hiiii")

    quote_ids = dao.get_all_quotes_ids()

    for quote_id in quote_ids:

        quote = dao.get_quote_by_id_legacy(quote_id)

        message = {
            "message": quote["message"],
            "user": quote["user"],
            "date": quote["date"],
        }

        quote["message"] = [message]

        logger.info(quote)

        dao.insert_quote(quote)


if __name__ == "__main__":
    main()
