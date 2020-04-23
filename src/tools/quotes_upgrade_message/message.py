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

# def get_quote_by_id_legacy(quote_id):
# 
#     quote = None
# 
#     try:
#         c.execute("""SELECT * FROM quotes WHERE id=:id""", {"id": quote_id})
#         query_result = c.fetchone()
# 
#         if query_result is not None:
#             quote = {}
#             quote["id"] = query_result[0]
#             quote["message"] = query_result[1]
#             quote["user"] = query_result[2]
#             quote["date"] = query_result[3]
# 
#     except Exception as e:
#         logger.error(
#             "Caught Error in dao.get_quote_by_id - {} \n {}", e, traceback.format_exc(),
#         )
# 
#     return quote
