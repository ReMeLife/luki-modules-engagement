"""
Database models for LUKi Engagement Module
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class UserInteraction(Base):
    """Model for tracking user interactions"""
    __tablename__ = "user_interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    session_id = Column(String(255), nullable=False, index=True)
    interaction_type = Column(String(100), nullable=False)  # chat, activity, feedback, etc.
    interaction_data = Column(JSON, nullable=True)  # Additional interaction details
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    duration_seconds = Column(Float, nullable=True)
    context = Column(JSON, nullable=True)  # Context information
    
    # Relationships
    metrics = relationship("EngagementMetric", back_populates="interaction")
    feedback_items = relationship("FeedbackItem", back_populates="interaction")


class EngagementMetric(Base):
    """Model for engagement metrics"""
    __tablename__ = "engagement_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    interaction_id = Column(Integer, ForeignKey("user_interactions.id"), nullable=True)
    metric_type = Column(String(100), nullable=False)  # engagement_score, activity_level, etc.
    metric_value = Column(Float, nullable=False)
    calculation_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    meta_data = Column(JSON, nullable=True)
    
    # Relationships
    interaction = relationship("UserInteraction", back_populates="metrics")


class FeedbackItem(Base):
    """Model for user feedback"""
    __tablename__ = "feedback_items"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    interaction_id = Column(Integer, ForeignKey("user_interactions.id"), nullable=True)
    feedback_type = Column(String(100), nullable=False)  # rating, comment, suggestion, etc.
    feedback_value = Column(Text, nullable=True)  # Text content or JSON string
    rating = Column(Float, nullable=True)  # Numeric rating if applicable
    sentiment_score = Column(Float, nullable=True)  # Calculated sentiment
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    processed = Column(Boolean, default=False)
    tags = Column(JSON, nullable=True)  # Categorization tags
    
    # Relationships
    interaction = relationship("UserInteraction", back_populates="feedback_items")


class SocialConnection(Base):
    """Model for social graph connections"""
    __tablename__ = "social_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id_1 = Column(String(255), nullable=False, index=True)
    user_id_2 = Column(String(255), nullable=False, index=True)
    connection_type = Column(String(100), nullable=False)  # similarity, shared_interest, etc.
    strength = Column(Float, nullable=False, default=0.0)  # Connection strength 0-1
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())
    meta_data = Column(JSON, nullable=True)  # Additional connection data
    active = Column(Boolean, default=True)


class EngagementSession(Base):
    """Model for engagement sessions"""
    __tablename__ = "engagement_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    session_id = Column(String(255), nullable=False, unique=True, index=True)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    total_interactions = Column(Integer, default=0)
    engagement_score = Column(Float, nullable=True)
    session_data = Column(JSON, nullable=True)  # Session context and metadata
    active = Column(Boolean, default=True)


class UserProfile(Base):
    """Model for user engagement profiles"""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False, unique=True, index=True)
    total_interactions = Column(Integer, default=0)
    avg_engagement_score = Column(Float, default=0.0)
    last_interaction = Column(DateTime(timezone=True), nullable=True)
    preferences = Column(JSON, nullable=True)  # User preferences
    engagement_patterns = Column(JSON, nullable=True)  # Behavioral patterns
    social_connections_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    active = Column(Boolean, default=True)