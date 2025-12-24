"""
Graph Views for Neo4j Graph Visualization

Provides endpoints for fetching graph data for visualization.
"""

import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .base_views import success_response, error_response, bad_request_response
from ..service_classes.graph_query_service import GraphQueryService
from ..service_classes.graph_entity_extractor import GraphEntityExtractor

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_graph_for_query(request):
    """
    Get graph visualization data for a query
    
    Returns nodes and edges for entities found in the query
    """
    try:
        query = request.data.get('query', '').strip()
        if not query:
            return bad_request_response('Query is required')
        
        max_nodes = int(request.data.get('max_nodes', 50))
        max_depth = int(request.data.get('max_depth', 2))  # 2-hop relationships
        
        graph_query_service = GraphQueryService()
        entity_extractor = GraphEntityExtractor()
        
        # Extract entities from query
        entities = entity_extractor.extract_entities(query)
        
        if not entities:
            return success_response("No entities found in query", {
                'nodes': [],
                'edges': [],
                'entities': []
            })
        
        # Get entity IDs
        entity_ids = [entity_extractor._generate_entity_id(e) for e in entities]
        
        # Build graph data
        nodes = []
        edges = []
        node_ids = set()
        
        # Get Neo4j service
        from ..service_classes.neo4j_service import get_neo4j_service
        neo4j = get_neo4j_service()
        
        # Query: Find entities and their relationships
        cypher_query = f"""
        MATCH path = (e:Entity)-[*1..{max_depth}]-(connected)
        WHERE e.id IN $entity_ids
        WITH e, connected, relationships(path) as rels
        LIMIT $max_nodes
        RETURN DISTINCT
            e.id AS entity_id,
            e.name AS entity_name,
            e.type AS entity_type,
            e.normalized_name AS entity_normalized,
            labels(connected)[0] AS connected_type,
            id(connected) AS connected_id,
            CASE 
                WHEN 'Entity' IN labels(connected) THEN connected.id
                WHEN 'Document' IN labels(connected) THEN connected.id
                ELSE toString(id(connected))
            END AS connected_node_id,
            CASE 
                WHEN 'Entity' IN labels(connected) THEN connected.name
                WHEN 'Document' IN labels(connected) THEN connected.filename
                ELSE toString(id(connected))
            END AS connected_name,
            CASE 
                WHEN 'Entity' IN labels(connected) THEN connected.type
                WHEN 'Document' IN labels(connected) THEN 'Document'
                ELSE labels(connected)[0]
            END AS connected_node_type,
            [rel IN rels | type(rel)] AS relationship_types
        """
        
        results = neo4j.execute_query(cypher_query, {
            'entity_ids': entity_ids,
            'max_nodes': max_nodes
        })
        
        # Process results to build nodes and edges
        for result in results:
            # Add query entity node
            entity_id = result.get('entity_id')
            if entity_id and entity_id not in node_ids:
                nodes.append({
                    'id': entity_id,
                    'label': result.get('entity_name', 'Unknown'),
                    'type': 'entity',
                    'entityType': result.get('entity_type', 'UNKNOWN'),
                    'group': 'query_entity',
                    'size': 20
                })
                node_ids.add(entity_id)
            
            # Add connected node
            connected_node_id = result.get('connected_node_id')
            connected_type = result.get('connected_type', 'Unknown')
            
            if connected_node_id and connected_node_id not in node_ids:
                if connected_type == 'Entity':
                    nodes.append({
                        'id': connected_node_id,
                        'label': result.get('connected_name', 'Unknown'),
                        'type': 'entity',
                        'entityType': result.get('connected_node_type', 'UNKNOWN'),
                        'group': 'related_entity',
                        'size': 15
                    })
                elif connected_type == 'Document':
                    nodes.append({
                        'id': connected_node_id,
                        'label': result.get('connected_name', 'Unknown Document'),
                        'type': 'document',
                        'group': 'document',
                        'size': 10
                    })
                node_ids.add(connected_node_id)
            
            # Add edge
            rel_types = result.get('relationship_types', [])
            if rel_types:
                edge_type = rel_types[0] if rel_types else 'RELATED_TO'
                edges.append({
                    'from': entity_id,
                    'to': connected_node_id,
                    'type': edge_type,
                    'label': edge_type.replace('_', ' ').title()
                })
        
        # Also get direct entity-to-entity relationships
        entity_rel_query = """
        MATCH (e1:Entity)-[r:RELATED_TO]-(e2:Entity)
        WHERE e1.id IN $entity_ids OR e2.id IN $entity_ids
        RETURN e1.id AS from_id, e2.id AS to_id, e1.name AS from_name, e2.name AS to_name,
               e1.type AS from_type, e2.type AS to_type, r.co_occurrence_count AS weight
        LIMIT 30
        """
        
        entity_results = neo4j.execute_query(entity_rel_query, {
            'entity_ids': entity_ids
        })
        
        for rel in entity_results:
            from_id = rel.get('from_id')
            to_id = rel.get('to_id')
            
            # Add nodes if not already present
            if from_id and from_id not in node_ids:
                nodes.append({
                    'id': from_id,
                    'label': rel.get('from_name', 'Unknown'),
                    'type': 'entity',
                    'entityType': rel.get('from_type', 'UNKNOWN'),
                    'group': 'related_entity',
                    'size': 15
                })
                node_ids.add(from_id)
            
            if to_id and to_id not in node_ids:
                nodes.append({
                    'id': to_id,
                    'label': rel.get('to_name', 'Unknown'),
                    'type': 'entity',
                    'entityType': rel.get('to_type', 'UNKNOWN'),
                    'group': 'related_entity',
                    'size': 15
                })
                node_ids.add(to_id)
            
            # Add edge
            if from_id and to_id:
                edges.append({
                    'from': from_id,
                    'to': to_id,
                    'type': 'RELATED_TO',
                    'label': 'Related To',
                    'weight': rel.get('weight', 1)
                })
        
        # Get entity info for display
        entity_info = [
            {
                'id': entity_extractor._generate_entity_id(e),
                'name': e.text,
                'type': e.entity_type,
                'normalized': e.normalized_text,
                'confidence': e.confidence
            }
            for e in entities
        ]
        
        return success_response("Graph data retrieved successfully", {
            'nodes': nodes,
            'edges': edges,
            'entities': entity_info,
            'stats': {
                'total_nodes': len(nodes),
                'total_edges': len(edges),
                'query_entities': len(entities)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting graph for query: {e}", exc_info=True)
        return error_response(f"Failed to retrieve graph data: {str(e)}")

