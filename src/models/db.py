from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logger.info("Creating Engine + Session...")
engine = create_engine("sqlite:///chaddi.db")
Session = sessionmaker()
Session.configure(bind=engine)
session = Session()

Base = declarative_base()

Base.metadata.create_all(engine)