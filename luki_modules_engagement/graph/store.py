"""
Graph storage and persistence using Neo4j/NetworkX adapters.
"""

from typing import Dict, List, Any, Optional, Union
import logging
import json
from datetime import datetime

import networkx as nx
from sqlalchemy.orm import Session

from ..config import EngagementConfig
from ..database import get_db_session
from ..models import SocialConnection

logger = logging.getLogger(__name__)


class GraphStore:
    """
    Handles storage and retrieval of graph data.
    Provides adapters for Neo4j and NetworkX persistence.
    """
    
    def __init__(self, config: Optional[EngagementConfig] = None):
        self.config = config or EngagementConfig()
        self.storage_backend = getattr(config, 'graph_storage_backend', 'networkx')
    
    def save_graph(self, graph: nx.Graph, graph_type: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Save graph to persistent storage.
        
        Args:
            graph: NetworkX graph to save
            graph_type: Type identifier ('social' or 'interest')
            metadata: Optional metadata about the graph
            
        Returns:
            Storage identifier for the saved graph
        """
        logger.info(f"Saving {graph_type} graph with {graph.number_of_nodes()} nodes")
        
        if self.storage_backend == 'neo4j':
            return self._save_to_neo4j(graph, graph_type, metadata)
        else:
            return self._save_to_networkx_format(graph, graph_type, metadata)
    
    def load_graph(self, graph_id: str, graph_type: str) -> Optional[nx.Graph]:
        """
        Load graph from persistent storage.
        
        Args:
            graph_id: Storage identifier
            graph_type: Type identifier ('social' or 'interest')
            
        Returns:
            Loaded NetworkX graph or None if not found
        """
        logger.info(f"Loading {graph_type} graph with ID {graph_id}")
        
        if self.storage_backend == 'neo4j':
            return self._load_from_neo4j(graph_id, graph_type)
        else:
            return self._load_from_networkx_format(graph_id, graph_type)
    
    def sync_social_connections_to_db(self, graph: nx.Graph) -> None:
        """
        Synchronize social graph connections back to the database.
        
        Args:
            graph: Social graph to synchronize
        """
        logger.info(f"Syncing {graph.number_of_edges()} connections to database")
        
        with get_db_session() as db:
            # Get existing connections
            existing_connections = {}
            for conn in db.query(SocialConnection).all():
                key = (conn.user_id_1, conn.user_id_2)
                existing_connections[key] = conn
            
            # Update from graph
            for edge in graph.edges(data=True):
                user1, user2, edge_data = edge
                
                # Ensure consistent ordering
                if user1 > user2:
                    user1, user2 = user2, user1
                
                key = (user1, user2)
                
                if key in existing_connections:
                    # Update existing connection
                    conn = existing_connections[key]
                    conn.strength = edge_data.get('strength', conn.strength)
                    conn.connection_type = edge_data.get('connection_type', conn.connection_type)
                    conn.meta_data = {
                        **(conn.meta_data or {}),
                        **edge_data.get('meta_data', {}),
                        'last_graph_sync': datetime.utcnow().isoformat()
                    }
                else:
                    # Create new connection
                    new_conn = SocialConnection(
                        user_id_1=user1,
                        user_id_2=user2,
                        connection_type=edge_data.get('connection_type', 'inferred'),
                        strength=edge_data.get('strength', 0.5),
                        meta_data={
                            **edge_data.get('meta_data', {}),
                            'created_from_graph': True,
                            'graph_sync': datetime.utcnow().isoformat()
                        },
                        active=True
                    )
                    db.add(new_conn)
            
            db.commit()
        
        logger.info("Social connections synchronized to database")
    
    def export_graph_data(self, graph: nx.Graph, format: str = 'json') -> Union[str, Dict[str, Any]]:
        """
        Export graph data in specified format.
        
        Args:
            graph: NetworkX graph to export
            format: Export format ('json', 'gexf', 'graphml')
            
        Returns:
            Exported graph data
        """
        logger.info(f"Exporting graph to {format} format")
        
        if format == 'json':
            return self._export_to_json(graph)
        elif format == 'gexf':
            return self._export_to_gexf(graph)
        elif format == 'graphml':
            return self._export_to_graphml(graph)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def import_graph_data(self, data: Union[str, Dict[str, Any]], format: str = 'json') -> nx.Graph:
        """
        Import graph data from specified format.
        
        Args:
            data: Graph data to import
            format: Data format ('json', 'gexf', 'graphml')
            
        Returns:
            Imported NetworkX graph
        """
        logger.info(f"Importing graph from {format} format")
        
        if format == 'json':
            return self._import_from_json(data)
        elif format == 'gexf':
            if not isinstance(data, str):
                raise ValueError("GEXF format requires string data")
            return self._import_from_gexf(data)
        elif format == 'graphml':
            if not isinstance(data, str):
                raise ValueError("GraphML format requires string data")
            return self._import_from_graphml(data)
        else:
            raise ValueError(f"Unsupported import format: {format}")
    
    def _save_to_networkx_format(self, graph: nx.Graph, graph_type: str, metadata: Optional[Dict[str, Any]]) -> str:
        """Save graph using NetworkX's built-in formats."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        graph_id = f"{graph_type}_{timestamp}"
        
        # Add metadata to graph
        if metadata:
            graph.graph.update(metadata)
        graph.graph['saved_at'] = datetime.utcnow().isoformat()
        graph.graph['graph_type'] = graph_type
        
        # For now, store as JSON in memory (could be extended to file system)
        graph_data = nx.node_link_data(graph)
        
        # Store in a simple in-memory cache (extend this for production)
        if not hasattr(self, '_graph_cache'):
            self._graph_cache = {}
        
        self._graph_cache[graph_id] = graph_data
        
        logger.info(f"Saved graph as {graph_id}")
        return graph_id
    
    def _load_from_networkx_format(self, graph_id: str, graph_type: str) -> Optional[nx.Graph]:
        """Load graph from NetworkX format."""
        if not hasattr(self, '_graph_cache') or graph_id not in self._graph_cache:
            logger.warning(f"Graph {graph_id} not found in cache")
            return None
        
        graph_data = self._graph_cache[graph_id]
        graph = nx.node_link_graph(graph_data)
        
        logger.info(f"Loaded graph {graph_id}")
        return graph
    
    def _save_to_neo4j(self, graph: nx.Graph, graph_type: str, metadata: Optional[Dict[str, Any]]) -> str:
        """Save graph to Neo4j database."""
        # TODO: Implement Neo4j integration
        logger.warning("Neo4j integration not yet implemented, falling back to NetworkX format")
        return self._save_to_networkx_format(graph, graph_type, metadata)
    
    def _load_from_neo4j(self, graph_id: str, graph_type: str) -> Optional[nx.Graph]:
        """Load graph from Neo4j database."""
        # TODO: Implement Neo4j integration
        logger.warning("Neo4j integration not yet implemented, falling back to NetworkX format")
        return self._load_from_networkx_format(graph_id, graph_type)
    
    def _export_to_json(self, graph: nx.Graph) -> Dict[str, Any]:
        """Export graph to JSON format."""
        return nx.node_link_data(graph)
    
    def _export_to_gexf(self, graph: nx.Graph) -> str:
        """Export graph to GEXF format."""
        try:
            import io
            buffer = io.StringIO()
            nx.write_gexf(graph, buffer)
            return buffer.getvalue()
        except Exception as e:
            logger.error(f"GEXF export failed: {e}")
            raise
    
    def _export_to_graphml(self, graph: nx.Graph) -> str:
        """Export graph to GraphML format."""
        try:
            import io
            buffer = io.StringIO()
            nx.write_graphml(graph, buffer)
            return buffer.getvalue()
        except Exception as e:
            logger.error(f"GraphML export failed: {e}")
            raise
    
    def _import_from_json(self, data: Union[str, Dict[str, Any]]) -> nx.Graph:
        """Import graph from JSON format."""
        if isinstance(data, str):
            data = json.loads(data)
        return nx.node_link_graph(data)
    
    def _import_from_gexf(self, data: str) -> nx.Graph:
        """Import graph from GEXF format."""
        try:
            import io
            buffer = io.StringIO(data)
            return nx.read_gexf(buffer)
        except Exception as e:
            logger.error(f"GEXF import failed: {e}")
            raise
    
    def _import_from_graphml(self, data: str) -> nx.Graph:
        """Import graph from GraphML format."""
        try:
            import io
            buffer = io.StringIO(data)
            return nx.read_graphml(buffer)
        except Exception as e:
            logger.error(f"GraphML import failed: {e}")
            raise
