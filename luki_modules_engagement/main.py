"""
FastAPI application for LUKi Engagement Module
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

from .config import EngagementConfig, get_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize configuration
config = get_config()

# Initialize FastAPI app
app = FastAPI(
    title="LUKi Engagement Module",
    description="Social engagement and recommendation system for LUKi",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components with error handling
try:
    # Import components only if they exist
    from .data import DataLoader
    from .graph import GraphBuilder
    from .recommend import RecommendationRanker
    from .interfaces import EngagementAPI
    
    data_loader = DataLoader()
    graph_builder = GraphBuilder()
    recommendation_ranker = RecommendationRanker()
    engagement_api = EngagementAPI()
    
    logger.info("Engagement modules initialized successfully")
    components_healthy = True
except ImportError as e:
    logger.warning(f"Some engagement components not available: {e}")
    data_loader = None
    graph_builder = None
    recommendation_ranker = None
    engagement_api = None
    components_healthy = False
except Exception as e:
    logger.error(f"Failed to initialize engagement modules: {e}")
    data_loader = None
    graph_builder = None
    recommendation_ranker = None
    engagement_api = None
    components_healthy = False

# Request/Response models
class InteractionRequest(BaseModel):
    user_id: str
    interaction_type: str
    content: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None

class InteractionResponse(BaseModel):
    interaction_id: str
    user_id: str
    status: str
    timestamp: str

class EngagementMetricsResponse(BaseModel):
    user_id: str
    engagement_score: float
    interaction_count: int
    last_active: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    version: str
    components: Dict[str, str]
    config: Dict[str, Any]

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Railway deployment"""
    components = {
        "data_loader": "healthy" if data_loader else "unavailable",
        "graph_builder": "healthy" if graph_builder else "unavailable", 
        "recommendation_ranker": "healthy" if recommendation_ranker else "unavailable",
        "engagement_api": "healthy" if engagement_api else "unavailable"
    }
    
    config_info = {
        "database_url": config.database_url,
        "interaction_tracking": config.enable_interaction_tracking,
        "api_port": config.api_port
    }
    
    return HealthResponse(
        status="healthy" if components_healthy else "degraded",
        version="1.0.0",
        components=components,
        config=config_info
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "LUKi Engagement Module",
        "version": "1.0.0",
        "status": "running",
        "endpoints": ["/health", "/interactions", "/metrics", "/recommendations"]
    }

# Track user interaction
@app.post("/interactions", response_model=InteractionResponse)
async def track_interaction(request: InteractionRequest):
    """Track a user interaction"""
    try:
        # Placeholder implementation
        interaction_id = f"int_{request.user_id}_{hash(request.interaction_type) % 10000}"
        
        return InteractionResponse(
            interaction_id=interaction_id,
            user_id=request.user_id,
            status="tracked",
            timestamp="2024-01-01T00:00:00Z"  # Use actual timestamp
        )
    except Exception as e:
        logger.error(f"Error tracking interaction: {e}")
        raise HTTPException(status_code=500, detail="Failed to track interaction")

# Get engagement metrics
@app.get("/metrics/{user_id}", response_model=EngagementMetricsResponse)
async def get_engagement_metrics(user_id: str):
    """Get engagement metrics for a user"""
    try:
        # Placeholder implementation
        return EngagementMetricsResponse(
            user_id=user_id,
            engagement_score=0.75,  # Mock score
            interaction_count=42,   # Mock count
            last_active="2024-01-01T00:00:00Z"
        )
    except Exception as e:
        logger.error(f"Error fetching engagement metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch engagement metrics")

# Get social recommendations
@app.get("/recommendations/{user_id}")
async def get_social_recommendations(user_id: str, limit: int = 5):
    """Get social engagement recommendations for a user"""
    try:
        # Placeholder implementation
        recommendations = [
            {
                "id": "rec_1",
                "type": "social_activity",
                "title": "Join Community Discussion",
                "description": "Participate in today's wellness discussion",
                "engagement_score": 0.8
            }
        ]
        
        return {"user_id": user_id, "recommendations": recommendations[:limit]}
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")

# Get user graph connections
@app.get("/graph/{user_id}")
async def get_user_connections(user_id: str):
    """Get user's social graph connections"""
    try:
        # Placeholder implementation
        connections = [
            {
                "user_id": "user_123",
                "connection_type": "similar_interests",
                "strength": 0.7
            }
        ]
        
        return {"user_id": user_id, "connections": connections}
    except Exception as e:
        logger.error(f"Error fetching user connections: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user connections")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", config.api_port))
    uvicorn.run(app, host=config.api_host, port=port)
