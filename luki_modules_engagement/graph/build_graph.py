"""
Graph building functionality for social-interest networks.
Creates and updates social-interest graphs using NetworkX.
"""

from typing import Dict, List, Any, Optional, Tuple, Set
import logging
from datetime import datetime, timedelta
from collections import defaultdict

import networkx as nx
import numpy as np
from sqlalchemy.orm import Session

from ..config import EngagementConfig
from ..database import get_db_session
from ..models import SocialConnection, UserInteraction, UserProfile
from ..data.schemas import InteractionSchema, SocialConnectionSchema

logger = logging.getLogger(__name__)


class GraphBuilder:
    """
    Builds and maintains social-interest graphs from user interaction data.
    Handles graph creation, updates, and community detection.
    """
    
    def __init__(self, config: Optional[EngagementConfig] = None):
        self.config = config or EngagementConfig()
        self.social_graph = nx.Graph()
        self.interest_graph = nx.DiGraph()
        
    def build_social_graph(self, user_ids: Optional[List[str]] = None) -> nx.Graph:
        """
        Build social connection graph from user interactions and explicit connections.
        
        Args:
            user_ids: Optional list to limit graph to specific users
            
        Returns:
            NetworkX graph with social connections
        """
        logger.info(f"Building social graph for {len(user_ids) if user_ids else 'all'} users")
        
        self.social_graph.clear()
        
        with get_db_session() as db:
            # Load explicit social connections
            query = db.query(SocialConnection).filter(SocialConnection.active == True)
            if user_ids:
                query = query.filter(
                    (SocialConnection.user_id_1.in_(user_ids)) |
                    (SocialConnection.user_id_2.in_(user_ids))
                )
            
            connections = query.all()
            
            # Add nodes and edges
            for conn in connections:
                # Add nodes with user attributes
                if not self.social_graph.has_node(conn.user_id_1):
                    self._add_user_node(db, conn.user_id_1)
                if not self.social_graph.has_node(conn.user_id_2):
                    self._add_user_node(db, conn.user_id_2)
                
                # Add edge with connection attributes
                self.social_graph.add_edge(
                    conn.user_id_1,
                    conn.user_id_2,
                    connection_type=conn.connection_type,
                    strength=conn.strength,
                    created_at=conn.created_at,
                    last_interaction=conn.last_interaction,
                    meta_data=conn.meta_data or {}
                )
            
            # Infer connections from interaction patterns
            self._infer_social_connections(db, user_ids)
        
        logger.info(f"Built social graph with {self.social_graph.number_of_nodes()} nodes and {self.social_graph.number_of_edges()} edges")
        return self.social_graph
    
    def build_interest_graph(self, user_ids: Optional[List[str]] = None) -> nx.DiGraph:
        """
        Build interest-based directed graph from user interactions.
        
        Args:
            user_ids: Optional list to limit graph to specific users
            
        Returns:
            NetworkX directed graph with interest connections
        """
        logger.info(f"Building interest graph for {len(user_ids) if user_ids else 'all'} users")
        
        self.interest_graph.clear()
        
        with get_db_session() as db:
            # Load user interactions to infer interests
            query = db.query(UserInteraction)
            if user_ids:
                query = query.filter(UserInteraction.user_id.in_(user_ids))
            
            # Focus on recent interactions for current interests
            recent_time = datetime.utcnow() - timedelta(days=30)
            interactions = query.filter(UserInteraction.timestamp >= recent_time).all()
            
            # Group interactions by user and extract interests
            user_interests = defaultdict(lambda: defaultdict(float))
            
            for interaction in interactions:
                interests = self._extract_interests_from_interaction(interaction)
                for interest, weight in interests.items():
                    user_interests[interaction.user_id][interest] += weight
            
            # Add nodes and edges based on interest similarity
            for user_id, interests in user_interests.items():
                if not self.interest_graph.has_node(user_id):
                    self._add_user_node_to_interest_graph(db, user_id, interests)
            
            # Create edges between users with similar interests
            self._create_interest_edges(dict(user_interests))
        
        logger.info(f"Built interest graph with {self.interest_graph.number_of_nodes()} nodes and {self.interest_graph.number_of_edges()} edges")
        return self.interest_graph
    
    def update_graph_incremental(self, new_interactions: List[InteractionSchema]) -> None:
        """
        Incrementally update graphs with new interaction data.
        
        Args:
            new_interactions: List of new interactions to process
        """
        logger.info(f"Updating graphs with {len(new_interactions)} new interactions")
        
        affected_users = set()
        
        for interaction in new_interactions:
            affected_users.add(interaction.user_id)
            
            # Update interest graph
            interests = self._extract_interests_from_interaction_schema(interaction)
            if self.interest_graph.has_node(interaction.user_id):
                node_data = self.interest_graph.nodes[interaction.user_id]
                current_interests = node_data.get('interests', {})
                
                # Update interest weights
                for interest, weight in interests.items():
                    current_interests[interest] = current_interests.get(interest, 0) + weight
                
                node_data['interests'] = current_interests
        
        # Rebuild edges for affected users in interest graph
        if affected_users:
            self._update_interest_edges_for_users(list(affected_users))
        
        logger.info(f"Updated graphs for {len(affected_users)} affected users")
    
    def detect_communities(self, graph_type: str = 'social') -> Dict[str, List[str]]:
        """
        Detect communities in the specified graph.
        
        Args:
            graph_type: 'social' or 'interest'
            
        Returns:
            Dictionary mapping community IDs to user lists
        """
        graph = self.social_graph if graph_type == 'social' else self.interest_graph
        
        if graph.number_of_nodes() == 0:
            return {}
        
        logger.info(f"Detecting communities in {graph_type} graph")
        
        # Use Louvain algorithm for community detection
        try:
            import networkx.algorithms.community as nx_comm
            communities = nx_comm.louvain_communities(graph.to_undirected() if isinstance(graph, nx.DiGraph) else graph)
            
            community_dict = {}
            for i, community in enumerate(communities):
                community_dict[f"community_{i}"] = list(community)
            
            logger.info(f"Detected {len(community_dict)} communities")
            return community_dict
            
        except Exception as e:
            logger.error(f"Community detection failed: {e}")
            return {}
    
    def _add_user_node(self, db: Session, user_id: str) -> None:
        """Add user node with profile attributes to social graph."""
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        node_attrs = {
            'user_id': user_id,
            'total_interactions': profile.total_interactions if profile else 0,
            'engagement_score': profile.engagement_score if profile else 0.0,
            'last_activity': profile.last_activity if profile else None
        }
        
        self.social_graph.add_node(user_id, **node_attrs)
    
    def _add_user_node_to_interest_graph(self, db: Session, user_id: str, interests: Dict[str, float]) -> None:
        """Add user node with interests to interest graph."""
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        node_attrs = {
            'user_id': user_id,
            'interests': interests,
            'total_interactions': profile.total_interactions if profile else 0,
            'engagement_score': profile.engagement_score if profile else 0.0
        }
        
        self.interest_graph.add_node(user_id, **node_attrs)
    
    def _infer_social_connections(self, db: Session, user_ids: Optional[List[str]]) -> None:
        """Infer social connections from interaction patterns."""
        # Look for users who interact frequently with similar content
        query = db.query(UserInteraction)
        if user_ids:
            query = query.filter(UserInteraction.user_id.in_(user_ids))
        
        # Group by interaction context to find co-occurring users
        recent_time = datetime.utcnow() - timedelta(days=7)
        interactions = query.filter(UserInteraction.timestamp >= recent_time).all()
        
        # Find users who interact with similar content
        content_users = defaultdict(set)
        for interaction in interactions:
            if interaction.context and 'content_id' in interaction.context:
                content_id = interaction.context['content_id']
                content_users[content_id].add(interaction.user_id)
        
        # Create inferred connections
        for content_id, users in content_users.items():
            if len(users) > 1:
                users_list = list(users)
                for i, user1 in enumerate(users_list):
                    for user2 in users_list[i+1:]:
                        if not self.social_graph.has_edge(user1, user2):
                            # Add weak inferred connection
                            self.social_graph.add_edge(
                                user1, user2,
                                connection_type='inferred',
                                strength=0.1,
                                inferred_from=content_id
                            )
    
    def _extract_interests_from_interaction(self, interaction: UserInteraction) -> Dict[str, float]:
        """Extract interests and weights from interaction."""
        interests = {}
        
        # Extract from interaction type
        if interaction.interaction_type:
            interests[f"type_{interaction.interaction_type}"] = 1.0
        
        # Extract from interaction data
        if interaction.interaction_data:
            for key, value in interaction.interaction_data.items():
                if isinstance(value, str) and len(value) < 50:  # Avoid long text
                    interests[f"data_{key}_{value}"] = 0.5
        
        # Weight by duration if available
        duration_weight = min(2.0, (interaction.duration_seconds or 1.0) / 60.0) if interaction.duration_seconds else 1.0
        
        return {k: v * duration_weight for k, v in interests.items()}
    
    def _extract_interests_from_interaction_schema(self, interaction: InteractionSchema) -> Dict[str, float]:
        """Extract interests from interaction schema."""
        interests = {}
        
        if interaction.interaction_type:
            interests[f"type_{interaction.interaction_type}"] = 1.0
        
        if interaction.data:
            for key, value in interaction.data.items():
                if isinstance(value, str) and len(value) < 50:
                    interests[f"data_{key}_{value}"] = 0.5
        
        duration_weight = min(2.0, (interaction.duration_seconds or 1.0) / 60.0) if interaction.duration_seconds else 1.0
        
        return {k: v * duration_weight for k, v in interests.items()}
    
    def _create_interest_edges(self, user_interests: Dict[str, Dict[str, float]]) -> None:
        """Create edges between users based on interest similarity."""
        users = list(user_interests.keys())
        
        for i, user1 in enumerate(users):
            for user2 in users[i+1:]:
                similarity = self._calculate_interest_similarity(
                    user_interests[user1],
                    user_interests[user2]
                )
                
                if similarity > 0.1:  # Threshold for creating edge
                    self.interest_graph.add_edge(
                        user1, user2,
                        similarity=similarity,
                        edge_type='interest_similarity'
                    )
                    # Add reverse edge for undirected similarity
                    self.interest_graph.add_edge(
                        user2, user1,
                        similarity=similarity,
                        edge_type='interest_similarity'
                    )
    
    def _calculate_interest_similarity(self, interests1: Dict[str, float], interests2: Dict[str, float]) -> float:
        """Calculate cosine similarity between two interest vectors."""
        if not interests1 or not interests2:
            return 0.0
        
        # Get all unique interests
        all_interests = set(interests1.keys()) | set(interests2.keys())
        
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
    
    def _update_interest_edges_for_users(self, user_ids: List[str]) -> None:
        """Update interest edges for specific users."""
        # Remove existing edges for these users
        edges_to_remove = []
        for edge in self.interest_graph.edges():
            if edge[0] in user_ids or edge[1] in user_ids:
                edges_to_remove.append(edge)
        
        self.interest_graph.remove_edges_from(edges_to_remove)
        
        # Rebuild edges
        user_interests = {}
        for user_id in user_ids:
            if self.interest_graph.has_node(user_id):
                user_interests[user_id] = self.interest_graph.nodes[user_id].get('interests', {})
        
        self._create_interest_edges(user_interests)
