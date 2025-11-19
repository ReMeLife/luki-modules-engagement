"""
FastAPI application for LUKi Engagement Module
"""

import os
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, cast
import logging

import httpx

from .config import EngagementConfig, get_config
from .database import get_db_session
from .models import UserInteraction
from .recommend.matcher import InterestMatcher

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

def _consent_checks_enabled() -> bool:
    """Return True if consent/policy checks should be applied for secondary uses."""
    return bool(getattr(config, "respect_consent_flags", True))


async def _enforce_engagement_policy(
    user_id: str,
    requested_scopes: Optional[List[str]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Call security service policy/enforce for engagement-related secondary uses.

    Defaults to requesting analytics and personalization scopes. When consent
    checks are disabled via configuration, this returns allowed=True without
    making an external call.
    """
    if not _consent_checks_enabled():
        return {"allowed": True, "reason": "consent_checks_disabled"}

    scopes = requested_scopes or ["analytics", "personalization"]

    payload: Dict[str, Any] = {
        "user_id": user_id,
        "requester_role": "engagement_service",
        "requested_scopes": scopes,
    }
    if context:
        payload["context"] = context

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{config.security_service_url}/policy/enforce",
                json=payload,
            )

        try:
            raw = response.json()
        except ValueError:
            raw = {"detail": response.text}

        data: Dict[str, Any]
        if isinstance(raw, dict):
            data = raw
        else:
            data = {"detail": raw}

        if response.status_code == 200:
            return {
                "allowed": bool(data.get("allowed", True)),
                "scopes_checked": data.get("scopes_checked", []),
                "reason": data.get("reason", "consent_valid"),
                "detail": data.get("detail"),
            }

        return {
            "allowed": False,
            "error": data.get("error", "policy_denied"),
            "detail": data.get("detail"),
            "status_code": response.status_code,
        }
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.error(
            "Engagement policy enforcement request failed",
            user_id=user_id,
            error=str(exc),
        )
        return {
            "allowed": False,
            "error": "policy_request_failed",
            "detail": str(exc),
        }


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
        db = get_db_session()
        try:
            if request.timestamp:
                try:
                    interaction_time = datetime.fromisoformat(request.timestamp)
                except ValueError:
                    interaction_time = datetime.utcnow()
            else:
                interaction_time = datetime.utcnow()
            session_id = f"session_{request.user_id}"
            interaction = UserInteraction(
                user_id=request.user_id,
                session_id=session_id,
                interaction_type=request.interaction_type,
                interaction_data=request.content or {},
                timestamp=interaction_time,
                context={}
            )
            db.add(interaction)
            db.commit()
            db.refresh(interaction)
        finally:
            db.close()
        return InteractionResponse(
            interaction_id=str(interaction.id),
            user_id=request.user_id,
            status="tracked",
            timestamp=interaction_time.isoformat()
        )
    except Exception as e:
        logger.error(f"Error tracking interaction: {e}")
        raise HTTPException(status_code=500, detail="Failed to track interaction")

# Get engagement metrics
@app.get("/metrics/{user_id}", response_model=EngagementMetricsResponse)
async def get_engagement_metrics(user_id: str):
    """Get engagement metrics for a user"""
    try:
        db = get_db_session()
        try:
            # Look back over recent interactions (last 30 days)
            now = datetime.utcnow()
            lookback_start = now - timedelta(days=30)
            from .models import UserInteraction as _UserInteraction
            interactions = (
                db.query(_UserInteraction)
                .filter(
                    _UserInteraction.user_id == user_id,
                    _UserInteraction.timestamp >= lookback_start,
                )
                .all()
            )
            interaction_count = len(interactions)
            timestamp_values = [
                cast(datetime, i.timestamp)
                for i in interactions
                if i.timestamp is not None
            ]
            last_active_dt = max(timestamp_values) if timestamp_values else None
            # Simple engagement score: combine volume and recency
            if interaction_count == 0:
                engagement_score = 0.0
                last_active_str = None
            else:
                last_active_str = last_active_dt.isoformat() if last_active_dt else None
                # Volume factor saturates at 50 interactions
                volume_factor = min(1.0, interaction_count / 50.0)
                # Recency factor: 1.0 if within 1 day, decays linearly to 0 over 30 days
                if last_active_dt:
                    days_since_last = max(
                        0.0,
                        (now - last_active_dt).total_seconds() / 86400.0,
                    )
                    recency_factor = max(0.0, 1.0 - days_since_last / 30.0)
                else:
                    recency_factor = 0.0
                engagement_score = round(0.7 * volume_factor + 0.3 * recency_factor, 3)
        finally:
            db.close()
        return EngagementMetricsResponse(
            user_id=user_id,
            engagement_score=engagement_score,
            interaction_count=interaction_count,
            last_active=last_active_str,
        )
    except Exception as e:
        logger.error(f"Error fetching engagement metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch engagement metrics")

# Get social recommendations
@app.get("/recommendations/{user_id}")
async def get_social_recommendations(user_id: str, limit: int = 5):
    """Get social engagement recommendations for a user"""
    try:
        policy = await _enforce_engagement_policy(
            user_id=user_id,
            context={"endpoint": "recommendations", "limit": limit},
        )
        if not policy.get("allowed", True):
            logger.info(
                "Social recommendations blocked by policy",
                user_id=user_id,
                policy_error=policy.get("error"),
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "error": policy.get("error", "consent_denied"),
                    "policy": policy,
                },
            )

        if recommendation_ranker is None:
            raise RuntimeError("Recommendation engine not available")
        matcher = InterestMatcher()
        # Find users with similar interests (overfetch, then rank and trim)
        similar_users = matcher.find_similar_users(user_id, limit=limit * 2)
        candidates = [
            {
                "user_id": similar_user_id,
                "similarity_score": similarity,
                "recommendation_type": "user_connection",
            }
            for similar_user_id, similarity in similar_users
        ]
        if not candidates:
            return {"user_id": user_id, "recommendations": []}
        ranked = recommendation_ranker.rank_user_recommendations(user_id, candidates)
        # Limit final recommendations and provide a clean response structure
        return {
            "user_id": user_id,
            "recommendations": ranked[:limit],
        }
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")

# Get user graph connections
@app.get("/graph/{user_id}")
async def get_user_connections(user_id: str):
    """Get user's social graph connections"""
    try:
        policy = await _enforce_engagement_policy(
            user_id=user_id,
            context={"endpoint": "graph"},
        )
        if not policy.get("allowed", True):
            logger.info(
                "User graph request blocked by policy",
                user_id=user_id,
                policy_error=policy.get("error"),
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "error": policy.get("error", "consent_denied"),
                    "policy": policy,
                },
            )

        if not graph_builder:
            raise RuntimeError("Graph builder not available")
        # Build social graph focused on this user
        graph = graph_builder.build_social_graph([user_id])
        connections = []
        node_info = None
        if user_id in graph:
            node_attrs = graph.nodes[user_id]
            last_activity_value = node_attrs.get("last_activity")
            if isinstance(last_activity_value, datetime):
                last_activity_str = last_activity_value.isoformat()
            else:
                last_activity_str = None
            node_info = {
                "user_id": user_id,
                "total_interactions": node_attrs.get("total_interactions", 0),
                "engagement_score": node_attrs.get("engagement_score", 0.0),
                "last_activity": last_activity_str,
            }
            for neighbor in graph.neighbors(user_id):
                edge_data = graph.get_edge_data(user_id, neighbor) or {}
                last_interaction_value = edge_data.get("last_interaction")
                if isinstance(last_interaction_value, datetime):
                    last_interaction_str = last_interaction_value.isoformat()
                else:
                    last_interaction_str = None
                connections.append({
                    "user_id": neighbor,
                    "connection_type": edge_data.get("connection_type", "inferred"),
                    "strength": edge_data.get("strength", 0.0),
                    "last_interaction": last_interaction_str,
                })
        return {
            "user_id": user_id,
            "node": node_info,
            "connections": connections,
        }
    except Exception as e:
        logger.error(f"Error fetching user connections: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user connections")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", config.api_port))
    uvicorn.run(app, host=config.api_host, port=port)
