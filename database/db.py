import enum
from datetime import datetime
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Enum, ForeignKey

engine = create_engine('sqlite:///database.db', echo=True)

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True)
    fname = Column(String)
    lname = Column(String)
    slack_username = Column(String)
    created_at = Column(DateTime, default=datetime.now())
    
class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(String, nullable=False)
    user_id = Column(String, ForeignKey('users.id'))
    role = Column(String, nullable=False)
    content = Column(String)
    docs_reffered = Column(String, nullable=True)
    pos_feedback = Column(Boolean, default=False)
    neg_feedback = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.now())

Base.metadata.create_all(engine)