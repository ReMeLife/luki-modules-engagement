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
from .interfaces import EngagementAgentTools, EngagementAPI

# Legacy components (for backward compatibility) - commented out until implemented
# from .interactions import InteractionTracker
# from .metrics import EngagementMetrics
# from .feedback import FeedbackCollector
# from .social_graph import SocialGraphAnalyzer

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
    
    # Legacy components - commented out until implemented
    # "InteractionTracker", 
    # "EngagementMetrics",
    # "FeedbackCollector",
    # "SocialGraphAnalyzer"
]