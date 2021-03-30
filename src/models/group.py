from sqlalchemy import Column, String, Table, ForeignKey
from sqlalchemy.orm import relationship

from models import Base

bakchod_group_association = Table(
    "bakchod_group",
    Base.metadata,
    Column("group_id", String, ForeignKey("group.tg_id")),
    Column("bakchod_id", String, ForeignKey("bakchod.tg_id")),
)


class Group(Base):
    __tablename__ = "groups"

    tg_id = Column(String, primary_key=True)
    title = Column(String)
    bakchods = relationship("Bakchod", secondary=bakchod_group_association)