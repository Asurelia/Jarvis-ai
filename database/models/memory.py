"""
Memory and embedding models for JARVIS AI
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, Index
from sqlalchemy.dialects.postgresql import VECTOR
from sqlalchemy.sql import func
from .base import BaseModel

class MemoryEntry(BaseModel):
    """Memory entry with vector embeddings"""
    __tablename__ = 'memory_entries'
    
    content = Column(Text, nullable=False)
    content_type = Column(String(50), default="text", nullable=False)  # text, image, audio, etc.
    category = Column(String(100), nullable=True)  # conversation, knowledge, experience, etc.
    
    # Vector embedding for semantic search
    embedding = Column(VECTOR(384), nullable=True)  # 384 dimensions for all-MiniLM-L6-v2
    
    # Importance and relevance scoring
    importance_score = Column(Float, default=0.5, nullable=False)
    access_count = Column(Integer, default=0, nullable=False)
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    
    # Context and relationships
    source_conversation_id = Column(Integer, nullable=True)
    related_entities = Column(JSON, default=list)  # List of related entity IDs
    tags = Column(JSON, default=list)  # List of tags for categorization
    
    # Metadata
    metadata = Column(JSON, default=dict)
    
    __table_args__ = (
        Index('idx_memory_category_importance', 'category', 'importance_score'),
        Index('idx_memory_access', 'last_accessed', 'access_count'),
        Index('idx_memory_embedding_cosine', 'embedding', postgresql_using='hnsw', 
              postgresql_with={'m': 16, 'ef_construction': 64}, postgresql_ops={'embedding': 'vector_cosine_ops'}),
    )
    
    def update_access(self):
        """Update access statistics"""
        self.access_count += 1
        self.last_accessed = func.now()

class EmbeddingCache(BaseModel):
    """Cache for computed embeddings"""
    __tablename__ = 'embedding_cache'
    
    hash_key = Column(String(64), unique=True, nullable=False, index=True)
    embedding = Column(VECTOR(384), nullable=False)
    model_name = Column(String(100), default="all-MiniLM-L6-v2", nullable=False)
    access_count = Column(Integer, default=1, nullable=False)
    last_accessed = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_embedding_cache_accessed', 'last_accessed', 'access_count'),
        Index('idx_embedding_cache_model', 'model_name', 'hash_key'),
    )