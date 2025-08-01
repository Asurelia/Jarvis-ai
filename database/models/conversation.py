"""
Conversation and Message models for JARVIS AI
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import BaseModel
import enum

class ConversationStatus(enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

class MessageRole(enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class Conversation(BaseModel):
    """Conversation entity"""
    __tablename__ = 'conversations'
    
    title = Column(String(255), nullable=False, default="New Conversation")
    status = Column(Enum(ConversationStatus), default=ConversationStatus.ACTIVE, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    persona_id = Column(String(50), nullable=True)  # JARVIS, FRIDAY, EDITH, etc.
    metadata = Column(JSON, default=dict)
    
    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    user = relationship("User", back_populates="conversations")
    
    @property
    def message_count(self):
        """Get message count for this conversation"""
        return len(self.messages)
    
    @property
    def last_message_at(self):
        """Get timestamp of last message"""
        if self.messages:
            return max(msg.created_at for msg in self.messages)
        return self.created_at

class Message(BaseModel):
    """Message entity"""
    __tablename__ = 'messages'
    
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    
    # AI specific fields
    model_used = Column(String(100), nullable=True)
    tokens_used = Column(Integer, default=0)
    processing_time = Column(Integer, default=0)  # milliseconds
    
    # Context and metadata
    context_data = Column(JSON, default=dict)
    metadata = Column(JSON, default=dict)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Message(id={self.id}, role={self.role.value}, content='{content_preview}')>"