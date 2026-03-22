"""
Pydantic models for users/events data validation and serialization.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator


class UserEventSchema(BaseModel):
    """Schema for user events from ELR slices and event feeds."""
    
    user_id: str = Field(..., description="User identifier")
    event_type: str = Field(..., description="Type of event")
    timestamp: datetime = Field(..., description="Event timestamp")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event data payload")
    context: Dict[str, Any] = Field(default_factory=dict, description="Event context")
    session_id: Optional[str] = Field(None, description="Associated session ID")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class InteractionSchema(BaseModel):
    """Schema for user interactions."""
    
    interaction_id: str = Field(..., description="Unique interaction identifier")
    user_id: str = Field(..., description="User identifier")
    interaction_type: str = Field(..., description="Type of interaction")
    timestamp: datetime = Field(..., description="Interaction timestamp")
    data: Dict[str, Any] = Field(default_factory=dict, description="Interaction data")
    duration_seconds: Optional[float] = Field(None, description="Interaction duration")
    context: Dict[str, Any] = Field(default_factory=dict, description="Interaction context")
    
    @validator('duration_seconds')
    def validate_duration(cls, v):
        if v is not None and v < 0:
            raise ValueError('Duration must be non-negative')
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FeedbackSchema(BaseModel):
    """Schema for user feedback data."""
    
    feedback_id: str = Field(..., description="Unique feedback identifier")
    user_id: str = Field(..., description="User identifier")
    feedback_type: str = Field(..., description="Type of feedback")
    content: str = Field(..., description="Feedback content")
    rating: Optional[int] = Field(None, description="Numeric rating")
    timestamp: datetime = Field(..., description="Feedback timestamp")
    context: Dict[str, Any] = Field(default_factory=dict, description="Feedback context")
    sentiment_score: Optional[float] = Field(None, description="Sentiment analysis score")
    tags: List[str] = Field(default_factory=list, description="Feedback tags")
    
    @validator('rating')
    def validate_rating(cls, v):
        if v is not None and not (1 <= v <= 5):
            raise ValueError('Rating must be between 1 and 5')
        return v
    
    @validator('sentiment_score')
    def validate_sentiment(cls, v):
        if v is not None and not (-1.0 <= v <= 1.0):
            raise ValueError('Sentiment score must be between -1.0 and 1.0')
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserProfileSchema(BaseModel):
    """Schema for user profile data."""
    
    user_id: str = Field(..., description="User identifier")
    total_interactions: int = Field(default=0, description="Total interaction count")
    total_sessions: int = Field(default=0, description="Total session count")
    avg_session_duration: Optional[float] = Field(None, description="Average session duration")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")
    engagement_score: Optional[float] = Field(None, description="Current engagement score")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    meta_data: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('engagement_score')
    def validate_engagement_score(cls, v):
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError('Engagement score must be between 0.0 and 1.0')
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SocialConnectionSchema(BaseModel):
    """Schema for social connections between users."""
    
    connection_id: str = Field(..., description="Unique connection identifier")
    user_id_1: str = Field(..., description="First user identifier")
    user_id_2: str = Field(..., description="Second user identifier")
    connection_type: str = Field(..., description="Type of connection")
    strength: float = Field(..., description="Connection strength")
    created_at: datetime = Field(..., description="Connection creation timestamp")
    last_interaction: Optional[datetime] = Field(None, description="Last interaction timestamp")
    meta_data: Dict[str, Any] = Field(default_factory=dict, description="Connection metadata")
    active: bool = Field(default=True, description="Whether connection is active")
    
    @validator('strength')
    def validate_strength(cls, v):
        if not (0.0 <= v <= 1.0):
            raise ValueError('Connection strength must be between 0.0 and 1.0')
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
