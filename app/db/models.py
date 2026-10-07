"""SQLAlchemy ORM models for VideoMind database."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import json

Base = declarative_base()


class Conversation(Base):
    """Represents a conversation/chat session."""
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    sources = relationship("ConversationSource", back_populates="conversation", cascade="all, delete-orphan")


class ConversationSource(Base):
    """Join table linking conversations to sources."""
    __tablename__ = "conversation_sources"

    id = Column(String(36), primary_key=True, index=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False, index=True)
    source_id = Column(String(36), ForeignKey("sources.id"), nullable=False, index=True)
    order_index = Column(Integer, default=0, nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="sources")
    source = relationship("Source", back_populates="conversations")


class Source(Base):
    """Represents an ingested source (video, audio, PDF, etc.)."""
    __tablename__ = "sources"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False)  # youtube, video, audio, pdf, text
    uri = Column(Text, nullable=True)  # URL or file path
    status = Column(String(50), default="processing", nullable=False)  # processing, ready, error
    metadata = Column(JSON, default={}, nullable=False)  # duration, pages, language, error_msg, etc.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    chunks = relationship("Chunk", back_populates="source", cascade="all, delete-orphan")
    conversations = relationship("ConversationSource", back_populates="source", cascade="all, delete-orphan")


class Chunk(Base):
    """Represents a processed chunk of text from a source."""
    __tablename__ = "chunks"

    id = Column(String(36), primary_key=True, index=True)
    source_id = Column(String(36), ForeignKey("sources.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)  # Position in source
    text = Column(Text, nullable=False)
    metadata = Column(JSON, default={}, nullable=False)  # timestamps, page_num, heading, etc.
    chroma_id = Column(String(255), nullable=True, unique=True)  # Reference to Chroma vector store
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    source = relationship("Source", back_populates="chunks")


class Message(Base):
    """Represents a message in a conversation."""
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, index=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String(50), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    citations = Column(JSON, default=[], nullable=False)  # [{source_id, ref_type, ref_value}, ...]
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
