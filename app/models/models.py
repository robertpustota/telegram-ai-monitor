from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, BigInteger, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class APIToken(Base):
    __tablename__ = "api_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)
    name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    telegram_session_id = Column(Integer, ForeignKey("telegram_sessions.id"), unique=True)
    telegram_session = relationship("TelegramSession", back_populates="api_token", uselist=False)


class TelegramSession(Base):
    """Model for storing Telegram sessions"""
    __tablename__ = "telegram_sessions"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True)
    session_string = Column(Text)
    api_id = Column(Integer)
    api_hash = Column(String)
    is_active = Column(Boolean, default=True)
    
    proxy_type = Column(Integer, nullable=True)
    proxy_host = Column(String, nullable=True)
    proxy_port = Column(Integer, nullable=True)
    proxy_username = Column(String, nullable=True)
    proxy_password = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    api_token = relationship("APIToken", back_populates="telegram_session", uselist=False)


class Channel(Base):
    """Model for storing channels"""
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    title = Column(String)
    channel_id = Column(BigInteger)
    session_id = Column(Integer, ForeignKey("telegram_sessions.id"))
    
    session = relationship("TelegramSession")
    topics = relationship("Topic", secondary="topic_channels", back_populates="channels")
    posts = relationship("Post", back_populates="channel")


class Topic(Base):
    """Model for storing topics"""
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String, nullable=True)
    
    channels = relationship("Channel", secondary="topic_channels", back_populates="topics")
    posts = relationship("Post", back_populates="topic")


class Post(Base):
    """Model for storing posts"""
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text)
    date = Column(DateTime(timezone=True))
    message_id = Column(BigInteger)
    
    channel_id = Column(Integer, ForeignKey("channels.id"))
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    
    channel = relationship("Channel", back_populates="posts")
    topic = relationship("Topic", back_populates="posts")

topic_channels = Table(
    "topic_channels",
    Base.metadata,
    Column("topic_id", Integer, ForeignKey("topics.id"), primary_key=True),
    Column("channel_id", Integer, ForeignKey("channels.id"), primary_key=True)
) 
