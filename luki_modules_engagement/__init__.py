"""
LUKi Engagement Module - Social engagement and recommendation system.
"""

from .config import EngagementConfig

# Data layer
from .data import DataLoader, UserEventSchema, InteractionSchema, FeedbackSchema

# Graph layer
from .graph import GraphBuilder, GraphMetrics, GraphStore

# Recommendation layer
from .recommend import InterestMatcher, RecommendationRanker, RecommendationExplainer

# Interface layer
try:
    from .interfaces import EngagementAgentTools, EngagementAPI
except ModuleNotFoundError:
    EngagementAgentTools = None
    EngagementAPI = None

__version__ = "1.0.0"

__all__ = [
    # Configuration
    "EngagementConfig",
    
    # Data layer
    "DataLoader",
    "UserEventSchema", 
    "InteractionSchema",
    "FeedbackSchema",
    
    # Graph layer
    "GraphBuilder",
    "GraphMetrics", 
    "GraphStore",
    
    # Recommendation layer
    "InterestMatcher",
    "RecommendationRanker",
    "RecommendationExplainer",
    
    # Interface layer
    "EngagementAgentTools",
    "EngagementAPI",
    
]