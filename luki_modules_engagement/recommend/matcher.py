"""
Interest and event matching logic for recommendations.
"""

from typing import Dict, List, Any, Optional, Tuple, Set
import logging
from datetime import datetime, timedelta
from collections import defaultdict

import numpy as np
import networkx as nx
from sqlalchemy.orm import Session

from ..config import EngagementConfig
from ..database import get_db_session
from ..models import UserInteraction, UserProfile, SocialConnection
from ..data.schemas import UserEventSchema, InteractionSchema

logger = logging.getLogger(__name__)


class InterestMatcher:
    """
    Matches users based on interests and interaction patterns.
    Provides interest/event matching logic for recommendations.
    """
    
    def __init__(self, config: Optional[EngagementConfig] = None):
        self.config = config or EngagementConfig()
        self.interest_threshold = 0.3
        self.recency_weight = 0.7
    
    def find_similar_users(self, user_id: str, limit: int = 10) -> List[Tuple[str, float]]:
        """
        Find users with similar interests to the given user.
        
        Args:
            user_id: Target user ID
            limit: Maximum number of similar users to return
            
        Returns:
            List of (user_id, similarity_score) tuples
        """
        logger.info(f"Finding similar users for {user_id}")
        
        # Get user's interest profile
        user_interests = self._get_user_interests(user_id)
        if not user_interests:
            logger.warning(f"No interests found for user {user_id}")
            return []
        
        # Get all other users' interests
        all_users_interests = self._get_all_users_interests(exclude_user=user_id)
        
        # Calculate similarities
        similarities = []
        for other_user_id, other_interests in all_users_interests.items():
            similarity = self._calculate_interest_similarity(user_interests, other_interests)
            if similarity > self.interest_threshold:
                similarities.append((other_user_id, similarity))
        
        # Sort by similarity and return top matches
        similarities.sort(key=lambda x: x[1], reverse=True)
        result = similarities[:limit]
        
        logger.info(f"Found {len(result)} similar users for {user_id}")
        return result
    
    def match_events_to_user(self, user_id: str, available_events: List[Dict[str, Any]], limit: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """
        Match events to user based on their interests and past interactions.
        
        Args:
            user_id: Target user ID
            available_events: List of event dictionaries
            limit: Maximum number of events to recommend
            
        Returns:
            List of (event, match_score) tuples
        """
        logger.info(f"Matching events for user {user_id}")
        
        user_interests = self._get_user_interests(user_id)
        if not user_interests:
            return []
        
        event_matches = []
        
        for event in available_events:
            match_score = self._calculate_event_match_score(user_interests, event)
            if match_score > 0.1:  # Minimum threshold
                event_matches.append((event, match_score))
        
        # Sort by match score and return top matches
        event_matches.sort(key=lambda x: x[1], reverse=True)
        result = event_matches[:limit]
        
        logger.info(f"Matched {len(result)} events for user {user_id}")
        return result
    
    def find_interest_communities(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Find communities of users with shared interests.
        
        Args:
            user_id: User to find communities for
            
        Returns:
            List of community dictionaries
        """
        logger.info(f"Finding interest communities for user {user_id}")
        
        # Get user's interests
        user_interests = self._get_user_interests(user_id)
        if not user_interests:
            return []
        
        # Find users with overlapping interests
        similar_users = self.find_similar_users(user_id, limit=50)
        
        if len(similar_users) < 2:
            return []
        
        # Build interest graph
        interest_graph = nx.Graph()
        interest_graph.add_node(user_id)
        
        for similar_user_id, similarity in similar_users:
            interest_graph.add_node(similar_user_id)
            interest_graph.add_edge(user_id, similar_user_id, weight=similarity)
        
        # Add edges between similar users
        for i, (user1, _) in enumerate(similar_users):
            for user2, _ in similar_users[i+1:]:
                user1_interests = self._get_user_interests(user1)
                user2_interests = self._get_user_interests(user2)
                similarity = self._calculate_interest_similarity(user1_interests, user2_interests)
                
                if similarity > self.interest_threshold:
                    interest_graph.add_edge(user1, user2, weight=similarity)
        
        # Detect communities
        try:
            import networkx.algorithms.community as nx_comm
            communities = list(nx_comm.louvain_communities(interest_graph))
            
            community_list = []
            for i, community in enumerate(communities):
                if user_id in community and len(community) > 1:
                    # Calculate shared interests for this community
                    shared_interests = self._find_shared_interests([self._get_user_interests(uid) for uid in community])
                    
                    community_dict = {
                        'community_id': f"interest_community_{i}",
                        'members': list(community),
                        'size': len(community),
                        'shared_interests': shared_interests,
                        'avg_similarity': np.mean([
                            interest_graph[u][v]['weight'] 
                            for u, v in interest_graph.edges(community) 
                            if u in community and v in community
                        ]) if len(community) > 1 else 0.0
                    }
                    community_list.append(community_dict)
            
            logger.info(f"Found {len(community_list)} interest communities for user {user_id}")
            return community_list
            
        except Exception as e:
            logger.error(f"Community detection failed: {e}")
            return []
    
    def recommend_connections(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Recommend new social connections based on interests and mutual connections.
        
        Args:
            user_id: User to recommend connections for
            limit: Maximum number of recommendations
            
        Returns:
            List of connection recommendation dictionaries
        """
        logger.info(f"Recommending connections for user {user_id}")
        
        recommendations = []
        
        # Get existing connections
        existing_connections = self._get_existing_connections(user_id)
        
        # Find similar users (potential connections)
        similar_users = self.find_similar_users(user_id, limit=20)
        
        for candidate_user_id, similarity in similar_users:
            if candidate_user_id in existing_connections:
                continue
            
            # Calculate recommendation score
            mutual_connections = self._count_mutual_connections(user_id, candidate_user_id, existing_connections)
            
            # Combine similarity and mutual connections
            recommendation_score = (similarity * 0.7) + (min(mutual_connections / 5.0, 1.0) * 0.3)
            
            # Get shared interests
            user_interests = self._get_user_interests(user_id)
            candidate_interests = self._get_user_interests(candidate_user_id)
            shared_interests = self._find_shared_interests([user_interests, candidate_interests])
            
            recommendation = {
                'user_id': candidate_user_id,
                'recommendation_score': recommendation_score,
                'similarity_score': similarity,
                'mutual_connections': mutual_connections,
                'shared_interests': shared_interests[:5],  # Top 5 shared interests
                'reason': self._generate_connection_reason(similarity, mutual_connections, shared_interests)
            }
            
            recommendations.append(recommendation)
        
        # Sort by recommendation score
        recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)
        result = recommendations[:limit]
        
        logger.info(f"Generated {len(result)} connection recommendations for user {user_id}")
        return result
    
    def _get_user_interests(self, user_id: str) -> Dict[str, float]:
        """Extract user interests from recent interactions."""
        interests = defaultdict(float)
        
        with get_db_session() as db:
            # Get recent interactions (last 30 days)
            recent_time = datetime.utcnow() - timedelta(days=30)
            interactions = db.query(UserInteraction).filter(
                UserInteraction.user_id == user_id,
                UserInteraction.timestamp >= recent_time
            ).all()
            
            for interaction in interactions:
                # Extract interests from interaction type
                if interaction.interaction_type:
                    interests[f"type_{interaction.interaction_type}"] += 1.0
                
                # Extract from interaction data
                if interaction.interaction_data:
                    for key, value in interaction.interaction_data.items():
                        if isinstance(value, str) and len(value) < 50:
                            interests[f"data_{key}_{value}"] += 0.5
                
                # Weight by recency
                days_ago = (datetime.utcnow() - interaction.timestamp).days
                recency_factor = max(0.1, 1.0 - (days_ago / 30.0))
                
                # Apply recency weight to all interests from this interaction
                for interest_key in list(interests.keys()):
                    if interest_key.startswith(('type_', 'data_')):
                        interests[interest_key] *= recency_factor
        
        # Normalize interests
        if interests:
            max_interest = max(interests.values())
            interests = {k: v / max_interest for k, v in interests.items()}
        
        return dict(interests)
    
    def _get_all_users_interests(self, exclude_user: Optional[str] = None) -> Dict[str, Dict[str, float]]:
        """Get interests for all users (except excluded one)."""
        all_interests = {}
        
        with get_db_session() as db:
            # Get all users with recent activity
            recent_time = datetime.utcnow() - timedelta(days=30)
            active_users = db.query(UserInteraction.user_id).filter(
                UserInteraction.timestamp >= recent_time
            ).distinct().all()
            
            for (user_id,) in active_users:
                if user_id != exclude_user:
                    all_interests[user_id] = self._get_user_interests(user_id)
        
        return all_interests
    
    def _calculate_interest_similarity(self, interests1: Dict[str, float], interests2: Dict[str, float]) -> float:
        """Calculate cosine similarity between two interest vectors."""
        if not interests1 or not interests2:
            return 0.0
        
        # Get all unique interests
        all_interests = set(interests1.keys()) | set(interests2.keys())
        
        if not all_interests:
            return 0.0
        
        # Create vectors
        vec1 = np.array([interests1.get(interest, 0.0) for interest in all_interests])
        vec2 = np.array([interests2.get(interest, 0.0) for interest in all_interests])
        
        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _calculate_event_match_score(self, user_interests: Dict[str, float], event: Dict[str, Any]) -> float:
        """Calculate how well an event matches user interests."""
        if not user_interests:
            return 0.0
        
        match_score = 0.0
        
        # Match event type
        event_type = event.get('type', '')
        if event_type and f"type_{event_type}" in user_interests:
            match_score += user_interests[f"type_{event_type}"] * 0.5
        
        # Match event tags/categories
        event_tags = event.get('tags', [])
        for tag in event_tags:
            if f"data_tag_{tag}" in user_interests:
                match_score += user_interests[f"data_tag_{tag}"] * 0.3
        
        # Match event description keywords
        description = event.get('description', '')
        if description:
            # Simple keyword matching (could be enhanced with NLP)
            words = description.lower().split()
            for word in words[:10]:  # Limit to first 10 words
                if f"data_keyword_{word}" in user_interests:
                    match_score += user_interests[f"data_keyword_{word}"] * 0.1
        
        return min(1.0, match_score)
    
    def _find_shared_interests(self, interest_lists: List[Dict[str, float]]) -> List[str]:
        """Find interests shared across multiple users."""
        if not interest_lists:
            return []
        
        # Find interests present in all lists
        shared_interests = set(interest_lists[0].keys())
        for interests in interest_lists[1:]:
            shared_interests &= set(interests.keys())
        
        # Sort by average strength across users
        shared_with_scores = []
        for interest in shared_interests:
            avg_score = np.mean([interests.get(interest, 0.0) for interests in interest_lists])
            shared_with_scores.append((interest, avg_score))
        
        shared_with_scores.sort(key=lambda x: x[1], reverse=True)
        return [interest for interest, _ in shared_with_scores]
    
    def _get_existing_connections(self, user_id: str) -> Set[str]:
        """Get set of existing connection user IDs."""
        connections = set()
        
        with get_db_session() as db:
            # Get connections where user is either user_id_1 or user_id_2
            db_connections = db.query(SocialConnection).filter(
                ((SocialConnection.user_id_1 == user_id) | (SocialConnection.user_id_2 == user_id)) &
                (SocialConnection.active == True)
            ).all()
            
            for conn in db_connections:
                other_user = conn.user_id_2 if conn.user_id_1 == user_id else conn.user_id_1
                connections.add(other_user)
        
        return connections
    
    def _count_mutual_connections(self, user1: str, user2: str, user1_connections: Set[str]) -> int:
        """Count mutual connections between two users."""
        user2_connections = self._get_existing_connections(user2)
        return len(user1_connections & user2_connections)
    
    def _generate_connection_reason(self, similarity: float, mutual_connections: int, shared_interests: List[str]) -> str:
        """Generate human-readable reason for connection recommendation."""
        reasons = []
        
        if similarity > 0.7:
            reasons.append("very similar interests")
        elif similarity > 0.5:
            reasons.append("similar interests")
        
        if mutual_connections > 0:
            reasons.append(f"{mutual_connections} mutual connection{'s' if mutual_connections > 1 else ''}")
        
        if shared_interests:
            top_interests = shared_interests[:2]
            if top_interests:
                clean_interests = [interest.replace('type_', '').replace('data_', '') for interest in top_interests]
                reasons.append(f"shared interest in {', '.join(clean_interests)}")
        
        return "; ".join(reasons) if reasons else "potential connection"
