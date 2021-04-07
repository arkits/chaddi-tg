from peewee import *
from playhouse.postgres_ext import *

import logging

logger = logging.getLogger("peewee")
logger.addHandler(logging.StreamHandler())
# logger.setLevel(logging.DEBUG)

# db = SqliteDatabase("chaddi.db")
db = PostgresqlExtDatabase("chaddi_tg")

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
    message_id = IntegerField()
    time_sent = DateTimeField()
    from_id = CharField()
    to_id = CharField()
    text = TextField(null=True)
    update = BinaryJSONField()


db.connect()
db.create_tables([Bakchod, Message])