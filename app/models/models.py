from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, BigInteger, Table, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import enum


class SourceType(enum.Enum):
    CHANNEL = "CHANNEL"
    GROUP = "GROUP"
    PRIVATE = "PRIVATE"


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
    sources = relationship("Source", back_populates="session")
    filters = relationship("Filter", back_populates="session")


class Message(Base):
    """Model for storing messages from various sources"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text)
    date = Column(DateTime(timezone=True))
    message_id = Column(BigInteger)
    
    source_id = Column(Integer, ForeignKey("sources.id"))
    filter_id = Column(Integer, ForeignKey("filters.id"), nullable=True)
    
    source = relationship("Source", back_populates="messages")
    filter = relationship("Filter", back_populates="messages")


class Source(Base):
    """Model for storing message sources (channels, groups, private chats)"""
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    title = Column(String)
    source_id = Column(BigInteger)
    source_type = Column(Enum(SourceType))
    session_id = Column(Integer, ForeignKey("telegram_sessions.id"))
    
    session = relationship("TelegramSession", back_populates="sources")
    filters = relationship("Filter", secondary="filter_sources", back_populates="sources")
    messages = relationship("Message", back_populates="source")


class Filter(Base):
    """Model for storing message filters"""
    __tablename__ = "filters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    prompt = Column(Text, nullable=True)  # Инструкция для модели о том, какие сообщения обрабатывать
    pattern = Column(String)  # Regex pattern or other filter pattern
    include_sources = Column(JSON, default=list)  # White list of sources
    exclude_sources = Column(JSON, default=list)  # Black list of sources
    session_id = Column(Integer, ForeignKey("telegram_sessions.id"))
    
    session = relationship("TelegramSession", back_populates="filters")
    sources = relationship("Source", secondary="filter_sources", back_populates="filters")
    messages = relationship("Message", back_populates="filter")


filter_sources = Table(
    "filter_sources",
    Base.metadata,
    Column("filter_id", Integer, ForeignKey("filters.id"), primary_key=True),
    Column("source_id", Integer, ForeignKey("sources.id"), primary_key=True)
) 
