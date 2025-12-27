import json

from peewee import *  # noqa: F403
from playhouse.postgres_ext import *  # noqa: F403

from src.domain import config

app_config = config.get_config()

if app_config.get("DB", "VERBOSE_LOGGING") == "true":
    import logging

    logger = logging.getLogger("peewee")
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)

# db = SqliteDatabase("chaddi.db")
db = PostgresqlExtDatabase(
    "chaddi_tg",
    user=str(app_config.get("DB", "USER")),
    password=str(app_config.get("DB", "PASSWORD")),
    host=str(app_config.get("DB", "HOST")),
)


# model definitions -- the standard "pattern" is to define a base model class
# that specifies which database to use.  then, any subclasses will automatically
# use the correct storage.
class BaseModel(Model):
    class Meta:
        database = db


EMPTY_JSON = "{}"
EMPTY_JSON = json.loads(EMPTY_JSON)


class Bakchod(BaseModel):
    tg_id = CharField(unique=True, primary_key=True)
    username = CharField(null=True)
    pretty_name = CharField(null=True)
    rokda = DoubleField(default=500)
    lastseen = DateTimeField(null=True)
    created = DateTimeField(null=True)
    updated = DateTimeField(null=True)
    metadata = BinaryJSONField(default=EMPTY_JSON)


class Message(BaseModel):
    id = AutoField()
    message_id = CharField()
    time_sent = DateTimeField()
    from_bakchod = ForeignKeyField(Bakchod, backref="messages")
    to_id = CharField()
    text = TextField(null=True)
    update = BinaryJSONField()


class Group(BaseModel):
    group_id = CharField(unique=True, primary_key=True)
    name = CharField(null=True)
    created = DateTimeField()
    updated = DateTimeField()
    metadata = BinaryJSONField(default=EMPTY_JSON)


class GroupMember(BaseModel):
    bakchod = ForeignKeyField(Bakchod, backref="group_member")
    group = ForeignKeyField(Group, backref="group_member")


class Quote(BaseModel):
    quote_id = CharField(unique=True, primary_key=True)
    message_id = CharField()
    created = DateTimeField()
    author_bakchod = ForeignKeyField(Bakchod, backref="quotes")
    quote_capture_bakchod = ForeignKeyField(Bakchod, backref="quotes_captured")
    quoted_in_group = ForeignKeyField(Group, backref="quotes")
    text = TextField(null=True)
    update = BinaryJSONField()


class Roll(BaseModel):
    roll_id = CharField(unique=True, primary_key=True)
    created = DateTimeField()
    updated = DateTimeField()
    expiry = DateTimeField()
    rule = CharField()
    goal = CharField()
    group = ForeignKeyField(Group, backref="roll")
    victim = ForeignKeyField(Bakchod, backref="roll_victim", null=True)
    winrar = ForeignKeyField(Bakchod, backref="roll_winrar", null=True)
    prize = CharField(null=True)


class ScheduledJob(BaseModel):
    job_id = AutoField()
    created = DateTimeField()
    updated = DateTimeField()
    from_bakchod = ForeignKeyField(Bakchod, backref="scheduled_jobs")
    group = ForeignKeyField(Group, backref="scheduled_jobs")
    job_context = BinaryJSONField(default=EMPTY_JSON)


class CommandUsage(BaseModel):
    id = AutoField()
    command_name = CharField()
    executed_at = DateTimeField()
    from_bakchod = ForeignKeyField(Bakchod, backref="command_usage", null=True)
    group = ForeignKeyField(Group, backref="command_usage", null=True)
    metadata = BinaryJSONField(default=EMPTY_JSON)


db.connect()
db.create_tables([Bakchod, Message, Group, GroupMember, Quote, Roll, ScheduledJob, CommandUsage])
