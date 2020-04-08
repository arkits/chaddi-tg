import sqlite3
from loguru import logger
import json
from models.bakchod import Bakchod
from models.group import Group
import traceback

chaddi_db = sqlite3.connect("db/chaddi.db", check_same_thread=False)
c = chaddi_db.cursor()


def init_db():

    try:
        c.execute(
            """CREATE TABLE IF NOT EXISTS bakchods (
                id text primary key,
                username text,
                first_name text,
                lastseen blob,
                rokda real,
                birthday blob,
                history blob,
                censored blob
            )"""
        )

        c.execute(
            """CREATE TABLE IF NOT EXISTS groups (
                id text primary key,
                title text,
                members blob
            )"""
        )

        c.execute(
            """CREATE TABLE IF NOT EXISTS quotes (
                id text primary key,
                message text,
                user text,
                date blob
            )"""
        )

        chaddi_db.commit()

        logger.info("DB Setup Complete!")

    except Exception as e:
        logger.error(
            "Caught Error in dao.init_db - {} \n {}", e, traceback.format_exc(),
        )


def insert_bakchod(bakchod):

    try:
        c.execute(
            """INSERT OR REPLACE INTO bakchods VALUES(
                :id,
                :username,
                :first_name,
                :lastseen,
                :rokda,
                :birthday,
                :history,
                :censored
            )""",
            {
                "id": bakchod.id,
                "username": bakchod.username,
                "first_name": bakchod.first_name,
                "lastseen": bakchod.lastseen,
                "rokda": bakchod.rokda,
                "birthday": bakchod.birthday,
                "history": json.dumps(bakchod.history),
                "censored": bakchod.censored,
            },
        )

        chaddi_db.commit()
    except Exception as e:
        logger.error(
            "Caught Error in dao.insert_bakchod - {} \n {}", e, traceback.format_exc(),
        )


def get_bakchod_by_id(bakchod_id):

    bakchod = None

    try:
        c.execute("""SELECT * FROM bakchods WHERE id=:id""", {"id": bakchod_id})
        query_result = c.fetchone()

        if query_result is not None:

            bakchod = Bakchod(query_result[0], query_result[1], query_result[2])
            bakchod.lastseen = query_result[3]
            bakchod.rokda = query_result[4]
            bakchod.birthday = query_result[5]
            bakchod.history = json.loads(query_result[6])
            bakchod.censored = bool(query_result[7])

    except Exception as e:

        logger.error(
            "Caught Error in dao.get_bakchod_by_id - {} \n {}",
            e,
            traceback.format_exc(),
        )

    return bakchod


def insert_group(group):

    try:
        c.execute(
            """INSERT OR REPLACE INTO groups VALUES(
                :id,
                :title,
                :members
            )""",
            {
                "id": group.id,
                "title": group.title,
                "members": json.dumps(group.members),
            },
        )

        chaddi_db.commit()
    except Exception as e:
        logger.error(
            "Caught Error in dao.insert_group - {} \n {}", e, traceback.format_exc(),
        )


def get_group_by_id(group_id):

    group = None

    try:
        c.execute("""SELECT * FROM groups WHERE id=:id""", {"id": group_id})
        query_result = c.fetchone()

        if query_result is not None:
            group = Group(query_result[0], query_result[1])
            group.members = json.loads(query_result[2])

    except Exception as e:
        logger.error(
            "Caught Error in dao.get_group_by_id - {} \n {}", e, traceback.format_exc(),
        )

    return group


def insert_quote(quote):

    try:
        c.execute(
            """INSERT OR REPLACE INTO quotes VALUES(
                :id,
                :message,
                :user,
                :date       
            )""",
            {
                "id": quote["id"],
                "message": quote["message"],
                "user": quote["user"],
                "date": quote["date"],
            },
        )

        chaddi_db.commit()
    except Exception as e:
        logger.error(
            "Caught Error in dao.insert_quote - {} \n {}", e, traceback.format_exc(),
        )


def get_quote_by_id(quote_id):

    quote = None

    try:
        c.execute("""SELECT * FROM quotes WHERE id=:id""", {"id": quote_id})
        query_result = c.fetchone()

        if query_result is not None:
            quote = {}
            quote["id"] = query_result[0]
            try:
                quote["message"] = query_result[1].decode("utf-8")
            except Exception as e:
                quote["message"] = query_result[1][2:-1]
                pass
            quote["user"] = query_result[2]
            quote["date"] = query_result[3]  # TODO: Cast to Python datetime

    except Exception as e:
        logger.error(
            "Caught Error in dao.get_quote_by_id - {} \n {}", e, traceback.format_exc(),
        )

    return quote


def get_all_quotes_ids():

    all_quote_ids = None

    try:
        c.execute("""SELECT id FROM quotes""")
        query_result = c.fetchall()

        if query_result is not None:
            all_quote_ids = []
            for q in query_result:
                all_quote_ids.append(q[0])

    except Exception as e:
        logger.error(
            "Caught Error in dao.get_all_quotes_ids - {} \n {}",
            e,
            traceback.format_exc(),
        )

    return all_quote_ids


def delete_quote_by_id(quote_id):

    try:
        c.execute("""DELETE FROM quotes WHERE id=:id""", {"id": quote_id})
        query_result = c.fetchall()
        chaddi_db.commit()
    except Exception as e:
        logger.error(
            "Caught Error in dao.get_quote_by_id - {} \n {}", e, traceback.format_exc(),
        )


init_db()