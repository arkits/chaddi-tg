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
    username = CharField(null=True, index=True)
    pretty_name = CharField(null=True)
    rokda = DoubleField(default=500)
    lastseen = DateTimeField(null=True, index=True)
    created = DateTimeField(null=True)
    updated = DateTimeField(null=True, index=True)
    metadata = BinaryJSONField(default=EMPTY_JSON)


class Message(BaseModel):
    id = AutoField()
    message_id = CharField()
    time_sent = DateTimeField(index=True)
    from_bakchod = ForeignKeyField(Bakchod, backref="messages", index=True)
    to_id = CharField(index=True)
    text = TextField(null=True)
    update = BinaryJSONField()

    class Meta:
        database = db
        indexes = ((("to_id", "time_sent"), False),)


class Group(BaseModel):
    group_id = CharField(unique=True, primary_key=True)
    name = CharField(null=True)
    created = DateTimeField()
    updated = DateTimeField()
    metadata = BinaryJSONField(default=EMPTY_JSON)


class GroupMember(BaseModel):
    bakchod = ForeignKeyField(Bakchod, backref="group_member", index=True)
    group = ForeignKeyField(Group, backref="group_member", index=True)

    class Meta:
        database = db
        indexes = ((("bakchod", "group"), True),)


class Quote(BaseModel):
    quote_id = CharField(unique=True, primary_key=True)
    message_id = CharField()
    created = DateTimeField(index=True)
    author_bakchod = ForeignKeyField(Bakchod, backref="quotes", index=True)
    quote_capture_bakchod = ForeignKeyField(Bakchod, backref="quotes_captured", index=True)
    quoted_in_group = ForeignKeyField(Group, backref="quotes", index=True)
    text = TextField(null=True)
    update = BinaryJSONField()


class Roll(BaseModel):
    roll_id = CharField(unique=True, primary_key=True)
    created = DateTimeField()
    updated = DateTimeField()
    expiry = DateTimeField(index=True)
    rule = CharField()
    goal = CharField()
    group = ForeignKeyField(Group, backref="roll", index=True)
    victim = ForeignKeyField(Bakchod, backref="roll_victim", null=True)
    winrar = ForeignKeyField(Bakchod, backref="roll_winrar", null=True)
    prize = CharField(null=True)


class ScheduledJob(BaseModel):
    job_id = AutoField()
    created = DateTimeField()
    updated = DateTimeField()
    from_bakchod = ForeignKeyField(Bakchod, backref="scheduled_jobs", index=True)
    group = ForeignKeyField(Group, backref="scheduled_jobs", index=True)
    job_context = BinaryJSONField(default=EMPTY_JSON)


class CommandUsage(BaseModel):
    id = AutoField()
    command_name = CharField(index=True)
    executed_at = DateTimeField(index=True)
    from_bakchod = ForeignKeyField(Bakchod, backref="command_usage", null=True, index=True)
    group = ForeignKeyField(Group, backref="command_usage", null=True, index=True)
    metadata = BinaryJSONField(default=EMPTY_JSON)

    class Meta:
        database = db
        indexes = (
            (("command_name", "group", "executed_at"), False),
            (("command_name", "from_bakchod", "executed_at"), False),
        )


db.connect()
db.create_tables([Bakchod, Message, Group, GroupMember, Quote, Roll, ScheduledJob, CommandUsage])
