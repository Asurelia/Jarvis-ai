"""
User and session models for JARVIS AI
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import BaseModel

class User(BaseModel):
    """User entity"""
    __tablename__ = 'users'
    
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    full_name = Column(String(200), nullable=True)
    
    # Authentication
    password_hash = Column(String(255), nullable=True)  # For local auth
    is_admin = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Preferences
    preferred_persona = Column(String(50), default="JARVIS", nullable=False)
    preferences = Column(JSON, default=dict)
    
    # Activity tracking
    last_login = Column(DateTime(timezone=True), nullable=True)
    login_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    sessions = relationship("Session", back_populates="user")
    
    def update_login(self):
        """Update login statistics"""
        self.last_login = func.now()
        self.login_count += 1

class Session(BaseModel):
    """User session tracking"""
    __tablename__ = 'sessions'
    
    user_id = Column(Integer, nullable=True)  # Allow anonymous sessions
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    
    # Session details
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    
    # Timing
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    
    # Security
    is_valid = Column(Boolean, default=True, nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoke_reason = Column(String(100), nullable=True)
    
    # Metadata
    metadata = Column(JSON, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    def is_expired(self):
        """Check if session is expired"""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) > self.expires_at
    
    def revoke(self, reason: str = "manual"):
        """Revoke session"""
        self.is_valid = False
        self.revoked_at = func.now()
        self.revoke_reason = reason