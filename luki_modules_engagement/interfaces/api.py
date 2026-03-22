"""
FastAPI endpoints for LUKi engagement module (optional).
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ..config import EngagementConfig
from ..data.loaders import DataLoader
from ..graph.build_graph import GraphBuilder
from ..graph.metrics import GraphMetrics
from ..recommend.matcher import InterestMatcher
from ..recommend.ranker import RecommendationRanker
from ..recommend.explainer import RecommendationExplainer

logger = logging.getLogger(__name__)


# Request/Response models
class UserRecommendationRequest(BaseModel):
    user_id: str
    limit: int = 5


class EventRecommendationRequest(BaseModel):
    user_id: str
    available_events: List[Dict[str, Any]]
    limit: int = 5


class GraphAnalysisRequest(BaseModel):
    user_ids: Optional[List[str]] = None
    graph_type: str = "social"


class ExplanationRequest(BaseModel):
    user_id: str
    recommendation_data: Dict[str, Any]
    recommended_user_id: Optional[str] = None
    event_data: Optional[Dict[str, Any]] = None


class EngagementAPI:
    """
    FastAPI application for LUKi engagement module endpoints.
    Provides REST API access to engagement functionality.
    """
    
    def __init__(self, config: Optional[EngagementConfig] = None):
        self.config = config or EngagementConfig()
        self.app = FastAPI(
            title="LUKi Engagement API",
            description="Social engagement and recommendation API for LUKi",
            version="1.0.0"
        )
        
        # Initialize components
        self.data_loader = DataLoader(config)
        self.graph_builder = GraphBuilder(config)
        self.graph_metrics = GraphMetrics(config)
        self.interest_matcher = InterestMatcher(config)
        self.ranker = RecommendationRanker(config)
        self.explainer = RecommendationExplainer(config)
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register all API routes."""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
        
        @self.app.post("/recommendations/users")
        async def get_user_recommendations(request: UserRecommendationRequest):
            """Get user recommendations based on interests and connections."""
            try:
                similar_users = self.interest_matcher.find_similar_users(request.user_id, request.limit)
                
                candidates = [
                    {
                        'user_id': similar_user_id,
                        'similarity_score': similarity,
                        'recommendation_type': 'user_connection'
                    }
                    for similar_user_id, similarity in similar_users
                ]
                
                ranked_candidates = self.ranker.rank_user_recommendations(request.user_id, candidates)
                
                return {
                    'status': 'success',
                    'user_id': request.user_id,
                    'recommendations': ranked_candidates,
                    'count': len(ranked_candidates)
                }
                
            except Exception as e:
                logger.error(f"Error getting user recommendations: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/recommendations/events")
        async def get_event_recommendations(request: EventRecommendationRequest):
            """Get event recommendations based on user interests."""
            try:
                event_matches = self.interest_matcher.match_events_to_user(
                    request.user_id, request.available_events, request.limit * 2
                )
                
                ranked_events = self.ranker.rank_event_recommendations(request.user_id, event_matches)
                
                return {
                    'status': 'success',
                    'user_id': request.user_id,
                    'recommendations': ranked_events[:request.limit],
                    'count': len(ranked_events[:request.limit])
                }
                
            except Exception as e:
                logger.error(f"Error getting event recommendations: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/recommendations/connections")
        async def get_connection_recommendations(request: UserRecommendationRequest):
            """Get social connection recommendations."""
            try:
                recommendations = self.interest_matcher.recommend_connections(
                    request.user_id, request.limit
                )
                
                return {
                    'status': 'success',
                    'user_id': request.user_id,
                    'recommendations': recommendations,
                    'count': len(recommendations)
                }
                
            except Exception as e:
                logger.error(f"Error getting connection recommendations: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/communities/{user_id}")
        async def get_user_communities(user_id: str):
            """Get interest communities for a user."""
            try:
                communities = self.interest_matcher.find_interest_communities(user_id)
                
                return {
                    'status': 'success',
                    'user_id': user_id,
                    'communities': communities,
                    'count': len(communities)
                }
                
            except Exception as e:
                logger.error(f"Error getting user communities: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/graph/analyze")
        async def analyze_graph(request: GraphAnalysisRequest):
            """Analyze social or interest graph structure."""
            try:
                if request.graph_type == "social":
                    graph = self.graph_builder.build_social_graph(request.user_ids)
                else:
                    graph = self.graph_builder.build_interest_graph(request.user_ids)
                
                centrality_metrics = self.graph_metrics.calculate_centrality_metrics(graph)
                community_structure = self.graph_metrics.analyze_community_structure(graph)
                network_health = self.graph_metrics.calculate_network_health_metrics(graph)
                
                return {
                    'status': 'success',
                    'graph_type': request.graph_type,
                    'nodes': graph.number_of_nodes(),
                    'edges': graph.number_of_edges(),
                    'centrality_metrics': centrality_metrics,
                    'community_structure': community_structure,
                    'network_health': network_health
                }
                
            except Exception as e:
                logger.error(f"Error analyzing graph: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/explanations")
        async def get_recommendation_explanation(request: ExplanationRequest):
            """Get explanation for a recommendation."""
            try:
                if request.recommended_user_id:
                    explanation = self.explainer.explain_user_recommendation(
                        request.user_id, request.recommended_user_id, request.recommendation_data
                    )
                elif request.event_data:
                    explanation = self.explainer.explain_event_recommendation(
                        request.user_id, request.event_data, request.recommendation_data
                    )
                else:
                    raise HTTPException(
                        status_code=400, 
                        detail="Must provide either recommended_user_id or event_data"
                    )
                
                return {
                    'status': 'success',
                    'explanation': explanation
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error generating explanation: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/users/{user_id}/engagement-summary")
        async def get_user_engagement_summary(user_id: str):
            """Get comprehensive engagement summary for a user."""
            try:
                from datetime import timedelta
                
                recent_events = self.data_loader.load_elr_slice(
                    user_id, 
                    datetime.utcnow() - timedelta(days=7),
                    datetime.utcnow()
                )
                
                social_graph = self.graph_builder.build_social_graph([user_id])
                influence_score = self.graph_metrics.calculate_engagement_influence_score(social_graph, user_id)
                
                communities = self.interest_matcher.find_interest_communities(user_id)
                
                return {
                    'status': 'success',
                    'user_id': user_id,
                    'recent_activity_count': len(recent_events),
                    'influence_score': influence_score,
                    'community_memberships': len(communities),
                    'communities': communities[:3],
                    'summary_generated_at': datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error getting engagement summary: {e}")
                raise HTTPException(status_code=500, detail=str(e))


def create_app(config: Optional[EngagementConfig] = None) -> FastAPI:
    """Create and configure FastAPI application."""
    api = EngagementAPI(config)
    return api.app
