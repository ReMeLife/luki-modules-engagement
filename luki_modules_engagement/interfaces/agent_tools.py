"""
LangChain @tool wrappers for LUKi agent integration.
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from langchain.tools import tool
from pydantic import BaseModel, Field

from ..config import EngagementConfig
from ..data.loaders import DataLoader
from ..graph.build_graph import GraphBuilder
from ..graph.metrics import GraphMetrics
from ..recommend.matcher import InterestMatcher
from ..recommend.ranker import RecommendationRanker
from ..recommend.explainer import RecommendationExplainer

logger = logging.getLogger(__name__)


class EngagementAgentTools:
    """
    LangChain tool wrappers for LUKi agent integration.
    Provides @tool decorated functions for agent use.
    """
    
    def __init__(self, config: Optional[EngagementConfig] = None):
        self.config = config or EngagementConfig()
        self.data_loader = DataLoader(config)
        self.graph_builder = GraphBuilder(config)
        self.graph_metrics = GraphMetrics(config)
        self.interest_matcher = InterestMatcher(config)
        self.ranker = RecommendationRanker(config)
        self.explainer = RecommendationExplainer(config)


# Tool input schemas
class UserRecommendationInput(BaseModel):
    user_id: str = Field(description="User ID to get recommendations for")
    limit: int = Field(default=5, description="Maximum number of recommendations")


class EventRecommendationInput(BaseModel):
    user_id: str = Field(description="User ID to get event recommendations for")
    available_events: List[Dict[str, Any]] = Field(description="List of available events")
    limit: int = Field(default=5, description="Maximum number of recommendations")


class CommunityAnalysisInput(BaseModel):
    user_id: str = Field(description="User ID to analyze communities for")


class GraphAnalysisInput(BaseModel):
    user_ids: Optional[List[str]] = Field(default=None, description="Optional list of user IDs to analyze")
    graph_type: str = Field(default="social", description="Type of graph: 'social' or 'interest'")


class ExplanationInput(BaseModel):
    user_id: str = Field(description="Target user ID")
    recommended_user_id: Optional[str] = Field(default=None, description="Recommended user ID")
    event_data: Optional[Dict[str, Any]] = Field(default=None, description="Event data")
    recommendation_data: Dict[str, Any] = Field(description="Recommendation data from previous steps")


# Initialize tools instance
_tools_instance = EngagementAgentTools()


@tool("find_similar_users", args_schema=UserRecommendationInput)
def find_similar_users(user_id: str, limit: int = 5) -> Dict[str, Any]:
    """
    Find users with similar interests and interaction patterns.
    
    Args:
        user_id: User ID to find similar users for
        limit: Maximum number of similar users to return
        
    Returns:
        Dictionary with similar users and their similarity scores
    """
    try:
        similar_users = _tools_instance.interest_matcher.find_similar_users(user_id, limit)
        
        # Rank the recommendations
        candidates = [
            {
                'user_id': similar_user_id,
                'similarity_score': similarity,
                'recommendation_type': 'user_connection'
            }
            for similar_user_id, similarity in similar_users
        ]
        
        ranked_candidates = _tools_instance.ranker.rank_user_recommendations(user_id, candidates)
        
        return {
            'status': 'success',
            'user_id': user_id,
            'similar_users': ranked_candidates,
            'count': len(ranked_candidates)
        }
        
    except Exception as e:
        logger.error(f"Error finding similar users: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'similar_users': []
        }


@tool("recommend_events", args_schema=EventRecommendationInput)
def recommend_events(user_id: str, available_events: List[Dict[str, Any]], limit: int = 5) -> Dict[str, Any]:
    """
    Recommend events based on user interests and preferences.
    
    Args:
        user_id: User ID to recommend events for
        available_events: List of available event dictionaries
        limit: Maximum number of event recommendations
        
    Returns:
        Dictionary with ranked event recommendations
    """
    try:
        # Get event matches
        event_matches = _tools_instance.interest_matcher.match_events_to_user(user_id, available_events, limit * 2)
        
        # Rank the recommendations
        ranked_events = _tools_instance.ranker.rank_event_recommendations(user_id, event_matches)
        
        return {
            'status': 'success',
            'user_id': user_id,
            'recommended_events': ranked_events[:limit],
            'count': len(ranked_events[:limit])
        }
        
    except Exception as e:
        logger.error(f"Error recommending events: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'recommended_events': []
        }


@tool("find_interest_communities", args_schema=CommunityAnalysisInput)
def find_interest_communities(user_id: str) -> Dict[str, Any]:
    """
    Find communities of users with shared interests.
    
    Args:
        user_id: User ID to find communities for
        
    Returns:
        Dictionary with interest communities
    """
    try:
        communities = _tools_instance.interest_matcher.find_interest_communities(user_id)
        
        return {
            'status': 'success',
            'user_id': user_id,
            'communities': communities,
            'count': len(communities)
        }
        
    except Exception as e:
        logger.error(f"Error finding interest communities: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'communities': []
        }


@tool("recommend_connections", args_schema=UserRecommendationInput)
def recommend_connections(user_id: str, limit: int = 5) -> Dict[str, Any]:
    """
    Recommend new social connections based on interests and mutual connections.
    
    Args:
        user_id: User ID to recommend connections for
        limit: Maximum number of connection recommendations
        
    Returns:
        Dictionary with connection recommendations
    """
    try:
        recommendations = _tools_instance.interest_matcher.recommend_connections(user_id, limit)
        
        return {
            'status': 'success',
            'user_id': user_id,
            'connection_recommendations': recommendations,
            'count': len(recommendations)
        }
        
    except Exception as e:
        logger.error(f"Error recommending connections: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'connection_recommendations': []
        }


@tool("analyze_social_graph", args_schema=GraphAnalysisInput)
def analyze_social_graph(user_ids: Optional[List[str]] = None, graph_type: str = "social") -> Dict[str, Any]:
    """
    Analyze social or interest graph structure and metrics.
    
    Args:
        user_ids: Optional list of user IDs to focus analysis on
        graph_type: Type of graph to analyze ('social' or 'interest')
        
    Returns:
        Dictionary with graph analysis results
    """
    try:
        # Build the appropriate graph
        if graph_type == "social":
            graph = _tools_instance.graph_builder.build_social_graph(user_ids)
        else:
            graph = _tools_instance.graph_builder.build_interest_graph(user_ids)
        
        # Calculate metrics
        centrality_metrics = _tools_instance.graph_metrics.calculate_centrality_metrics(graph)
        community_structure = _tools_instance.graph_metrics.analyze_community_structure(graph)
        network_health = _tools_instance.graph_metrics.calculate_network_health_metrics(graph)
        
        return {
            'status': 'success',
            'graph_type': graph_type,
            'nodes': graph.number_of_nodes(),
            'edges': graph.number_of_edges(),
            'centrality_metrics': centrality_metrics,
            'community_structure': community_structure,
            'network_health': network_health
        }
        
    except Exception as e:
        logger.error(f"Error analyzing graph: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'graph_type': graph_type
        }


@tool("explain_recommendation", args_schema=ExplanationInput)
def explain_recommendation(user_id: str, recommendation_data: Dict[str, Any], 
                         recommended_user_id: Optional[str] = None, 
                         event_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generate explanation for why a recommendation was made.
    
    Args:
        user_id: Target user ID
        recommendation_data: Data from the recommendation process
        recommended_user_id: Optional recommended user ID for user recommendations
        event_data: Optional event data for event recommendations
        
    Returns:
        Dictionary with recommendation explanation
    """
    try:
        if recommended_user_id:
            # User recommendation explanation
            explanation = _tools_instance.explainer.explain_user_recommendation(
                user_id, recommended_user_id, recommendation_data
            )
        elif event_data:
            # Event recommendation explanation
            explanation = _tools_instance.explainer.explain_event_recommendation(
                user_id, event_data, recommendation_data
            )
        else:
            return {
                'status': 'error',
                'error': 'Must provide either recommended_user_id or event_data'
            }
        
        return {
            'status': 'success',
            'explanation': explanation
        }
        
    except Exception as e:
        logger.error(f"Error generating explanation: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }


@tool("get_user_engagement_summary")
def get_user_engagement_summary(user_id: str) -> Dict[str, Any]:
    """
    Get comprehensive engagement summary for a user.
    
    Args:
        user_id: User ID to get summary for
        
    Returns:
        Dictionary with user engagement summary
    """
    try:
        # Load recent user data
        from datetime import timedelta
        recent_events = _tools_instance.data_loader.load_elr_slice(
            user_id, 
            datetime.utcnow() - timedelta(days=7),
            datetime.utcnow()
        )
        
        # Get social graph position
        social_graph = _tools_instance.graph_builder.build_social_graph([user_id])
        influence_score = _tools_instance.graph_metrics.calculate_engagement_influence_score(social_graph, user_id)
        
        # Get interest communities
        communities = _tools_instance.interest_matcher.find_interest_communities(user_id)
        
        return {
            'status': 'success',
            'user_id': user_id,
            'recent_activity_count': len(recent_events),
            'influence_score': influence_score,
            'community_memberships': len(communities),
            'communities': communities[:3],  # Top 3 communities
            'summary_generated_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting engagement summary: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'user_id': user_id
        }


# Export all tools for LangChain agent registration
ENGAGEMENT_TOOLS = [
    find_similar_users,
    recommend_events,
    find_interest_communities,
    recommend_connections,
    analyze_social_graph,
    explain_recommendation,
    get_user_engagement_summary
]
