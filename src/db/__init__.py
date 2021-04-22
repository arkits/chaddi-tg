from domain import config

from peewee import *
from playhouse.postgres_ext import *

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


class Bakchod(BaseModel):
    tg_id = CharField(unique=True, primary_key=True)
    username = CharField(null=True)
    pretty_name = CharField(null=True)
    rokda = DoubleField(default=500)
    lastseen = DateTimeField(null=True)
    created = DateTimeField(null=True)
    updated = DateTimeField(null=True)


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


class GroupMember(BaseModel):
    bakchod = ForeignKeyField(Bakchod, backref="group_member")
    group = ForeignKeyField(Group, backref="group_member")


db.connect()
db.create_tables([Bakchod, Message, Group, GroupMember])