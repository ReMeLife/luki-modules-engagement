"""
Graph metrics and analysis for centrality, community detection, and engagement scoring.
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
from collections import defaultdict

import networkx as nx
import numpy as np
from sqlalchemy.orm import Session

from ..config import EngagementConfig
from ..database import get_db_session
from ..models import EngagementMetric, UserProfile

logger = logging.getLogger(__name__)


class GraphMetrics:
    """
    Calculates graph-based metrics for social and interest networks.
    Provides centrality measures, community analysis, and engagement scoring.
    """
    
    def __init__(self, config: Optional[EngagementConfig] = None):
        self.config = config or EngagementConfig()
    
    def calculate_centrality_metrics(self, graph: nx.Graph) -> Dict[str, Dict[str, float]]:
        """
        Calculate various centrality metrics for all nodes in the graph.
        
        Args:
            graph: NetworkX graph to analyze
            
        Returns:
            Dictionary mapping user IDs to centrality metrics
        """
        logger.info(f"Calculating centrality metrics for graph with {graph.number_of_nodes()} nodes")
        
        if graph.number_of_nodes() == 0:
            return {}
        
        metrics = {}
        
        try:
            # Degree centrality
            degree_centrality = nx.degree_centrality(graph)
            
            # Betweenness centrality (sample for large graphs)
            if graph.number_of_nodes() > 1000:
                betweenness_centrality = nx.betweenness_centrality(graph, k=min(100, graph.number_of_nodes()))
            else:
                betweenness_centrality = nx.betweenness_centrality(graph)
            
            # Closeness centrality
            closeness_centrality = nx.closeness_centrality(graph)
            
            # Eigenvector centrality (if graph is connected)
            try:
                eigenvector_centrality = nx.eigenvector_centrality(graph, max_iter=1000)
            except (nx.NetworkXError, np.linalg.LinAlgError):
                # Fallback for disconnected graphs
                eigenvector_centrality = {node: 0.0 for node in graph.nodes()}
            
            # PageRank
            pagerank = nx.pagerank(graph)
            
            # Combine all metrics
            for node in graph.nodes():
                metrics[node] = {
                    'degree_centrality': degree_centrality.get(node, 0.0),
                    'betweenness_centrality': betweenness_centrality.get(node, 0.0),
                    'closeness_centrality': closeness_centrality.get(node, 0.0),
                    'eigenvector_centrality': eigenvector_centrality.get(node, 0.0),
                    'pagerank': pagerank.get(node, 0.0)
                }
            
            logger.info(f"Calculated centrality metrics for {len(metrics)} nodes")
            
        except Exception as e:
            logger.error(f"Error calculating centrality metrics: {e}")
            return {}
        
        return metrics
    
    def analyze_community_structure(self, graph: nx.Graph) -> Dict[str, Any]:
        """
        Analyze community structure and calculate community-related metrics.
        
        Args:
            graph: NetworkX graph to analyze
            
        Returns:
            Dictionary with community analysis results
        """
        logger.info("Analyzing community structure")
        
        if graph.number_of_nodes() < 2:
            return {'communities': {}, 'modularity': 0.0, 'num_communities': 0}
        
        try:
            import networkx.algorithms.community as nx_comm
            
            # Detect communities using Louvain algorithm
            communities = nx_comm.louvain_communities(graph)
            
            # Calculate modularity
            modularity = nx_comm.modularity(graph, communities)
            
            # Convert communities to dictionary format
            community_dict = {}
            node_to_community = {}
            
            for i, community in enumerate(communities):
                community_id = f"community_{i}"
                community_dict[community_id] = {
                    'members': list(community),
                    'size': len(community),
                    'density': self._calculate_community_density(graph, community)
                }
                
                for node in community:
                    node_to_community[node] = community_id
            
            # Calculate inter-community connections
            inter_community_edges = 0
            for edge in graph.edges():
                if node_to_community.get(edge[0]) != node_to_community.get(edge[1]):
                    inter_community_edges += 1
            
            result = {
                'communities': community_dict,
                'node_to_community': node_to_community,
                'modularity': modularity,
                'num_communities': len(communities),
                'inter_community_edges': inter_community_edges,
                'average_community_size': np.mean([len(c) for c in communities]) if communities else 0
            }
            
            logger.info(f"Found {len(communities)} communities with modularity {modularity:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"Community analysis failed: {e}")
            return {'communities': {}, 'modularity': 0.0, 'num_communities': 0}
    
    def calculate_engagement_influence_score(self, graph: nx.Graph, user_id: str) -> float:
        """
        Calculate engagement influence score based on graph position and connections.
        
        Args:
            graph: NetworkX graph
            user_id: User to calculate score for
            
        Returns:
            Engagement influence score (0.0 to 1.0)
        """
        if not graph.has_node(user_id):
            return 0.0
        
        try:
            # Get centrality metrics
            centrality_metrics = self.calculate_centrality_metrics(graph)
            user_metrics = centrality_metrics.get(user_id, {})
            
            # Weighted combination of centrality measures
            weights = {
                'degree_centrality': 0.3,
                'betweenness_centrality': 0.25,
                'closeness_centrality': 0.2,
                'eigenvector_centrality': 0.15,
                'pagerank': 0.1
            }
            
            influence_score = sum(
                user_metrics.get(metric, 0.0) * weight
                for metric, weight in weights.items()
            )
            
            # Normalize to 0-1 range
            return min(1.0, max(0.0, influence_score))
            
        except Exception as e:
            logger.error(f"Error calculating influence score for {user_id}: {e}")
            return 0.0
    
    def find_bridge_users(self, graph: nx.Graph, communities: Dict[str, List[str]]) -> List[str]:
        """
        Find users who act as bridges between communities.
        
        Args:
            graph: NetworkX graph
            communities: Dictionary of community memberships
            
        Returns:
            List of bridge user IDs
        """
        logger.info("Finding bridge users between communities")
        
        if len(communities) < 2:
            return []
        
        # Create node to community mapping
        node_to_community = {}
        for community_id, members in communities.items():
            for member in members:
                node_to_community[member] = community_id
        
        bridge_users = []
        
        for node in graph.nodes():
            if node not in node_to_community:
                continue
            
            user_community = node_to_community[node]
            connected_communities = set()
            
            # Check neighbors' communities
            for neighbor in graph.neighbors(node):
                neighbor_community = node_to_community.get(neighbor)
                if neighbor_community and neighbor_community != user_community:
                    connected_communities.add(neighbor_community)
            
            # User is a bridge if connected to multiple other communities
            if len(connected_communities) >= 2:
                bridge_users.append(node)
        
        logger.info(f"Found {len(bridge_users)} bridge users")
        return bridge_users
    
    def calculate_network_health_metrics(self, graph: nx.Graph) -> Dict[str, float]:
        """
        Calculate overall network health and connectivity metrics.
        
        Args:
            graph: NetworkX graph to analyze
            
        Returns:
            Dictionary of network health metrics
        """
        logger.info("Calculating network health metrics")
        
        if graph.number_of_nodes() == 0:
            return {'connectivity': 0.0, 'density': 0.0, 'clustering': 0.0, 'efficiency': 0.0}
        
        try:
            # Basic connectivity metrics
            density = nx.density(graph)
            
            # Clustering coefficient
            clustering = nx.average_clustering(graph)
            
            # Global efficiency (for connected components)
            efficiency = 0.0
            if nx.is_connected(graph):
                efficiency = nx.global_efficiency(graph)
            else:
                # Average efficiency of connected components
                components = list(nx.connected_components(graph))
                if components:
                    component_efficiencies = []
                    for component in components:
                        subgraph = graph.subgraph(component)
                        if len(component) > 1:
                            component_efficiencies.append(nx.global_efficiency(subgraph))
                    efficiency = np.mean(component_efficiencies) if component_efficiencies else 0.0
            
            # Connectivity (fraction of nodes in largest component)
            if graph.number_of_nodes() > 1:
                largest_component_size = len(max(nx.connected_components(graph), key=len))
                connectivity = largest_component_size / graph.number_of_nodes()
            else:
                connectivity = 1.0
            
            return {
                'connectivity': connectivity,
                'density': density,
                'clustering': clustering,
                'efficiency': efficiency,
                'num_components': nx.number_connected_components(graph),
                'average_degree': np.mean([d for n, d in graph.degree()]) if graph.number_of_edges() > 0 else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error calculating network health metrics: {e}")
            return {'connectivity': 0.0, 'density': 0.0, 'clustering': 0.0, 'efficiency': 0.0}
    
    def store_graph_metrics(self, user_metrics: Dict[str, Dict[str, float]], metric_type: str = 'centrality') -> None:
        """
        Store calculated graph metrics in the database.
        
        Args:
            user_metrics: Dictionary of user metrics to store
            metric_type: Type of metrics being stored
        """
        logger.info(f"Storing {metric_type} metrics for {len(user_metrics)} users")
        
        with get_db_session() as db:
            for user_id, metrics in user_metrics.items():
                for metric_name, value in metrics.items():
                    # Create or update metric record
                    existing_metric = db.query(EngagementMetric).filter(
                        EngagementMetric.user_id == user_id,
                        EngagementMetric.metric_name == f"{metric_type}_{metric_name}"
                    ).first()
                    
                    if existing_metric:
                        existing_metric.metric_value = value
                        existing_metric.calculated_at = db.execute("SELECT NOW()").scalar()
                    else:
                        new_metric = EngagementMetric(
                            user_id=user_id,
                            metric_name=f"{metric_type}_{metric_name}",
                            metric_value=value,
                            metric_type=metric_type,
                            meta_data={'source': 'graph_analysis'}
                        )
                        db.add(new_metric)
            
            db.commit()
        
        logger.info(f"Stored {metric_type} metrics successfully")
    
    def _calculate_community_density(self, graph: nx.Graph, community: set) -> float:
        """Calculate the density of connections within a community."""
        if len(community) < 2:
            return 0.0
        
        subgraph = graph.subgraph(community)
        return nx.density(subgraph)
