"""
Neo4j Graph Database Service

This service provides a connection interface to Neo4j for Graph RAG functionality.
Handles entity storage, relationship creation, and graph queries.
"""

import logging
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from django.conf import settings

logger = logging.getLogger(__name__)


class Neo4jConnectionError(Exception):
    """Exception raised when Neo4j connection is not available"""
    pass


class Neo4jService:
    """Service for interacting with Neo4j graph database"""
    
    def __init__(self):
        """Initialize Neo4j connection"""
        try:
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            logger.info(f"Neo4j driver initialized: {settings.NEO4J_URI}")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j driver: {e}")
            self.driver = None
    
    def close(self):
        """Close Neo4j driver connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j driver closed")
    
    def test_connection(self) -> bool:
        """Test connection to Neo4j"""
        if not self.driver:
            return False
        
        try:
            with self.driver.session(database=settings.NEO4J_DATABASE) as session:
                result = session.run("RETURN 1 AS test")
                record = result.single()
                return record["test"] == 1 if record else False
        except Exception as e:
            logger.error(f"Neo4j connection test failed: {e}")
            return False
    
    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results
        
        Args:
            query: Cypher query string
            parameters: Optional query parameters
            
        Returns:
            List of dictionaries containing query results
            
        Raises:
            Neo4jConnectionError: If Neo4j driver is not initialized or connection fails
        """
        if not self.driver:
            error_msg = "Neo4j driver not initialized - check Neo4j connection settings"
            logger.error(error_msg)
            raise Neo4jConnectionError(error_msg)
        
        # Test connection before executing query
        if not self.test_connection():
            error_msg = "Neo4j connection test failed - service may be unavailable"
            logger.error(error_msg)
            raise Neo4jConnectionError(error_msg)
        
        try:
            with self.driver.session(database=settings.NEO4J_DATABASE) as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Error executing Neo4j query: {e}")
            logger.error(f"Query: {query[:200]}...")  # Truncate long queries
            logger.error(f"Parameters: {parameters}")
            # Re-raise as Neo4jConnectionError for better error handling upstream
            raise Neo4jConnectionError(f"Neo4j query execution failed: {str(e)}") from e
    
    def execute_write_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> bool:
        """
        Execute a write query (CREATE, UPDATE, DELETE, MERGE)
        
        Args:
            query: Cypher query string
            parameters: Optional query parameters
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            Neo4jConnectionError: If Neo4j driver is not initialized or connection fails
        """
        if not self.driver:
            error_msg = "Neo4j driver not initialized - check Neo4j connection settings"
            logger.error(error_msg)
            raise Neo4jConnectionError(error_msg)
        
        # Test connection before executing query
        if not self.test_connection():
            error_msg = "Neo4j connection test failed - service may be unavailable"
            logger.error(error_msg)
            raise Neo4jConnectionError(error_msg)
        
        try:
            with self.driver.session(database=settings.NEO4J_DATABASE) as session:
                session.run(query, parameters or {})
                return True
        except Exception as e:
            logger.error(f"Error executing Neo4j write query: {e}")
            logger.error(f"Query: {query[:200]}...")  # Truncate long queries
            logger.error(f"Parameters: {parameters}")
            # Re-raise as Neo4jConnectionError for better error handling upstream
            raise Neo4jConnectionError(f"Neo4j write query execution failed: {str(e)}") from e
    
    def create_constraints(self):
        """Create common constraints and indexes for better performance"""
        constraints = [
            # Unique constraints
            "CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
            
            # Indexes for common queries
            "CREATE INDEX document_type_index IF NOT EXISTS FOR (d:Document) ON (d.type)",
            "CREATE INDEX entity_type_index IF NOT EXISTS FOR (e:Entity) ON (e.type)",
            "CREATE INDEX entity_name_index IF NOT EXISTS FOR (e:Entity) ON (e.name)",
            "CREATE INDEX entity_embedding_index IF NOT EXISTS FOR (e:Entity) ON (e.embedding)",
        ]
        
        for constraint in constraints:
            try:
                self.execute_write_query(constraint)
                logger.info(f"Created constraint/index: {constraint[:50]}...")
            except Exception as e:
                logger.warning(f"Could not create constraint/index (may already exist): {e}")
        
        # Try to create vector index if Neo4j version supports it (5.11+)
        self._create_vector_index_if_supported()
    
    def _create_vector_index_if_supported(self):
        """Create vector index for entity embeddings if Neo4j version supports it"""
        try:
            # Check Neo4j version
            version_query = "CALL dbms.components() YIELD name, versions, edition RETURN versions[0] AS version"
            version_result = self.execute_query(version_query)
            
            if version_result:
                version_str = version_result[0].get('version', '')
                # Parse version (e.g., "5.11.0" -> [5, 11])
                try:
                    major, minor = map(int, version_str.split('.')[:2])
                    if major > 5 or (major == 5 and minor >= 11):
                        # Neo4j 5.11+ supports vector indexes
                        vector_index_query = """
                        CREATE VECTOR INDEX entity_embedding_vector IF NOT EXISTS
                        FOR (e:Entity) ON e.embedding
                        OPTIONS {
                            indexConfig: {
                                `vector.dimensions`: 1024,
                                `vector.similarity_function`: 'cosine'
                            }
                        }
                        """
                        self.execute_write_query(vector_index_query)
                        logger.info("Created vector index for entity embeddings")
                except (ValueError, IndexError):
                    logger.debug(f"Could not parse Neo4j version: {version_str}")
        except Exception as e:
            logger.debug(f"Vector index creation not supported or failed: {e}")
            # Not a critical error - fallback to Python-based similarity
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get basic statistics about the graph"""
        stats_query = """
        MATCH (n)
        WITH labels(n)[0] AS label, count(n) AS count
        RETURN label, count
        ORDER BY count DESC
        """
        
        relationship_query = """
        MATCH ()-[r]->()
        WITH type(r) AS relationship_type, count(*) AS count
        RETURN relationship_type, count
        ORDER BY count DESC
        """
        
        try:
            nodes = self.execute_query(stats_query)
            relationships = self.execute_query(relationship_query)
            
            # Get entity type breakdown
            entity_type_query = """
            MATCH (e:Entity)
            WITH e.type AS entity_type, count(e) AS count
            RETURN entity_type, count
            ORDER BY count DESC
            """
            entity_types = self.execute_query(entity_type_query)
            
            total_nodes = sum(node.get('count', 0) for node in nodes)
            total_relationships = sum(rel.get('count', 0) for rel in relationships)
            
            return {
                'nodes': nodes,
                'relationships': relationships,
                'entity_types': entity_types,
                'total_nodes': total_nodes,
                'total_relationships': total_relationships,
            }
        except Exception as e:
            logger.error(f"Error getting graph stats: {e}")
            return {
                'nodes': [],
                'relationships': [],
                'entity_types': [],
                'total_nodes': 0,
                'total_relationships': 0,
            }


# Global service instance
neo4j_service = None

def get_neo4j_service() -> Neo4jService:
    """Get or create Neo4j service instance"""
    global neo4j_service
    if neo4j_service is None:
        neo4j_service = Neo4jService()
    return neo4j_service

