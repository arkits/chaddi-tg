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
                modifiers blob
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

        c.execute(
            """CREATE TABLE IF NOT EXISTS daans (
                id text primary key,
                sender text,
                receiver text,
                amount real,
                date blob
            )"""
        )

        c.execute(
            """CREATE TABLE IF NOT EXISTS rolls (
                group_id text primary key,
                rule text,
                roll_number text,
                victim text,
                winrar text,
                expiry blob
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
                :modifiers
            )""",
            {
                "id": bakchod.id,
                "username": bakchod.username,
                "first_name": bakchod.first_name,
                "lastseen": bakchod.lastseen,
                "rokda": bakchod.rokda,
                "birthday": bakchod.birthday,
                "history": json.dumps(bakchod.history, default=str),
                "modifiers": json.dumps(bakchod.modifiers, default=str),
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
            bakchod.modifiers = json.loads(query_result[7])

    except Exception as e:

        logger.error(
            "Caught Error in dao.get_bakchod_by_id - {} \n {}",
            e,
            traceback.format_exc(),
        )

    return bakchod


def get_bakchod_by_username(username):

    bakchod = None

    try:
        c.execute(
            """SELECT * FROM bakchods WHERE username=:username""",
            {"username": username},
        )
        query_result = c.fetchone()

        if query_result is not None:

            bakchod = Bakchod(query_result[0], query_result[1], query_result[2])
            bakchod.lastseen = query_result[3]
            bakchod.rokda = query_result[4]
            bakchod.birthday = query_result[5]
            bakchod.history = json.loads(query_result[6])
            bakchod.modifiers = json.loads(query_result[7])

    except Exception as e:

        logger.error(
            "Caught Error in dao.get_bakchod_by_username - {} \n {}",
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

            # Santize Group Members
            members_str = []
            members = json.loads(query_result[2])
            for id in members:
                if str(id) not in members_str:
                    members_str.append(str(id))
            group.members = members_str

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
            quote["message"] = sanitize_quote_message(query_result[1])
            quote["user"] = query_result[2]
            quote["date"] = query_result[3]

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


def sanitize_quote_message(message):

    if isinstance(message, (bytes, bytearray)):
        return str(message, "utf-8")
    else:
        if message.startswith("b'"):
            trimed = message[2:-1]
            return trimed

    return message


def get_daan_by_id(daan_id):

    daan = None

    try:
        c.execute("""SELECT * FROM daans WHERE id=:id""", {"id": daan_id})
        query_result = c.fetchone()

        if query_result is not None:

            daan = {}
            daan["id"] = query_result[0]
            daan["sender"] = query_result[1]
            daan["receiver"] = query_result[2]
            daan["amount"] = query_result[3]
            daan["date"] = query_result[4]

    except Exception as e:

        logger.error(
            "Caught Error in dao.get_daan_by_id - {} \n {}", e, traceback.format_exc(),
        )

    return daan


def insert_daan(id, sender_id, receiver_id, amount, date):

    try:
        c.execute(
            """INSERT OR REPLACE INTO daans VALUES(
                :id,
                :sender,
                :receiver,
                :amount,
                :date
            )""",
            {
                "id": id,
                "sender": sender_id,
                "receiver": receiver_id,
                "amount": amount,
                "date": date,
            },
        )

        chaddi_db.commit()
    except Exception as e:
        logger.error(
            "Caught Error in dao.insert_daan - {} \n {}", e, traceback.format_exc(),
        )


def get_roll_by_id(group_id):

    roll = None

    try:
        c.execute(
            """SELECT * FROM rolls WHERE group_id=:group_id""", {"group_id": group_id}
        )
        query_result = c.fetchone()

        if query_result is not None:

            roll = {}
            roll["group_id"] = query_result[0]
            roll["rule"] = query_result[1]
            roll["roll_number"] = query_result[2]
            roll["victim"] = query_result[3]
            roll["winrar"] = query_result[4]
            roll["expiry"] = query_result[5]

    except Exception as e:

        logger.error(
            "Caught Error in dao.get_roll_by_id - {} \n {}", e, traceback.format_exc(),
        )

    return roll


def insert_roll(group_id, rule, roll_number, victim, winrar, expiry):

    try:
        c.execute(
            """INSERT OR REPLACE INTO rolls VALUES(
                :group_id,
                :rule,
                :roll_number,
                :victim,
                :winrar,
                :expiry
            )""",
            {
                "group_id": group_id,
                "rule": rule,
                "roll_number": roll_number,
                "victim": victim,
                "winrar": winrar,
                "expiry": expiry,
            },
        )

        chaddi_db.commit()
    except Exception as e:
        logger.error(
            "Caught Error in dao.insert_roll - {} \n {}", e, traceback.format_exc(),
        )


def get_all_bakchods():

    bakchods = None

    try:
        c.execute("""SELECT * FROM bakchods""")
        query_results = c.fetchall()

        if query_results is not None:

            bakchods = []

            for query_result in query_results:

                bakchod = Bakchod(query_result[0], query_result[1], query_result[2])
                bakchod.lastseen = query_result[3]
                bakchod.rokda = query_result[4]
                bakchod.birthday = query_result[5]
                bakchod.history = json.loads(query_result[6])
                bakchod.modifiers = json.loads(query_result[7])

                bakchods.append(bakchod)

    except Exception as e:

        logger.error(
            "Caught Error in dao.get_all_bakchods - {} \n {}",
            e,
            traceback.format_exc(),
        )

    return bakchods


init_db()
