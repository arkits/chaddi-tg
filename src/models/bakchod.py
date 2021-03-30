from sqlalchemy import Column, String, Float, Date

from models import Base


class Bakchod(Base):

    __tablename__ = "bakchods"

    tg_id = Column(String, primary_key=True, nullable=False)
    first_name = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    username = Column(String, nullable=True)
    rokda = Column(Float, nullable=False)
    lastseen = Column(Date, nullable=False)
