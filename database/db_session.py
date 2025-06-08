from database.db import engine, User, ChatHistory
from sqlalchemy.orm import sessionmaker

Session = sessionmaker(bind=engine)
session = Session()

def get_session():
    return session