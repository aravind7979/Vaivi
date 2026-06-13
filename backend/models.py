from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    shortcut_keys = Column(String, default="Ctrl+Shift+Space")
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    chats = relationship("Chat", back_populates="user")
    memories = relationship("LongTermMemory", back_populates="user", cascade="all, delete-orphan")

class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    role = Column(String, nullable=False) # 'user' or 'ai'
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    chat = relationship("Chat", back_populates="messages")

class LongTermMemory(Base):
    __tablename__ = "long_term_memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    memory_text = Column(String, nullable=False)
    memory_type = Column(String, default="general") # e.g. preference, goal, profile
    importance = Column(Integer, default=1)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    user = relationship("User", back_populates="memories")
