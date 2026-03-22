"""
Configuration management for LUKi Engagement Module
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class EngagementConfig(BaseSettings):
    """Configuration for the LUKi Engagement Module"""
    
    # Database settings
    database_url: str = Field(
        default="sqlite:///./engagement.db",
        alias="ENGAGEMENT_DATABASE_URL",
        description="Database connection URL"
    )
    
    # Redis settings for caching
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        alias="ENGAGEMENT_REDIS_URL", 
        description="Redis connection URL"
    )
    
    # Interaction tracking settings
    enable_interaction_tracking: bool = Field(
        default=True,
        alias="ENGAGEMENT_ENABLE_INTERACTION_TRACKING",
        description="Enable interaction tracking"
    )
    
    interaction_batch_size: int = Field(
        default=100,
        alias="ENGAGEMENT_INTERACTION_BATCH_SIZE",
        description="Batch size for interaction processing"
    )
    
    # Metrics calculation settings
    metrics_calculation_interval: int = Field(
        default=3600,  # 1 hour
        alias="ENGAGEMENT_METRICS_INTERVAL",
        description="Metrics calculation interval in seconds"
    )
    
    engagement_threshold_low: float = Field(
        default=0.3,
        alias="ENGAGEMENT_THRESHOLD_LOW",
        description="Low engagement threshold"
    )
    
    engagement_threshold_high: float = Field(
        default=0.7,
        alias="ENGAGEMENT_THRESHOLD_HIGH", 
        description="High engagement threshold"
    )
    
    # Feedback settings
    feedback_retention_days: int = Field(
        default=365,
        alias="ENGAGEMENT_FEEDBACK_RETENTION_DAYS",
        description="Feedback retention period in days"
    )
    
    # Social graph settings
    social_graph_max_connections: int = Field(
        default=1000,
        alias="ENGAGEMENT_SOCIAL_GRAPH_MAX_CONNECTIONS",
        description="Maximum connections in social graph"
    )
    
    social_similarity_threshold: float = Field(
        default=0.5,
        alias="ENGAGEMENT_SOCIAL_SIMILARITY_THRESHOLD",
        description="Similarity threshold for social connections"
    )
    
    # Security & privacy
    security_service_url: str = Field(
        default="http://localhost:8103",
        alias="ENGAGEMENT_SECURITY_SERVICE_URL",
        description="URL for LUKi Security & Privacy Service"
    )
    respect_consent_flags: bool = Field(
        default=True,
        alias="ENGAGEMENT_RESPECT_CONSENT_FLAGS",
        description="Respect user consent flags for secondary uses such as social recommendations and engagement nudges"
    )
    
    # API settings
    api_host: str = Field(
        default="0.0.0.0",
        alias="ENGAGEMENT_API_HOST",
        description="API host address"
    )
    
    api_port: int = Field(
        default=8003,
        alias="ENGAGEMENT_API_PORT",
        description="API port number"
    )
    
    # Logging
    log_level: str = Field(
        default="INFO",
        alias="ENGAGEMENT_LOG_LEVEL",
        description="Logging level"
    )
    
    model_config = {
        "extra": "ignore",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "env_prefix": "",
        "case_sensitive": False
    }


# Global config instance
config = EngagementConfig()


def get_config() -> EngagementConfig:
    """Get the global configuration instance"""
    return config