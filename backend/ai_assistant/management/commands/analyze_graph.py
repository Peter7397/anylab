"""
Django management command to analyze the Neo4j knowledge graph

Shows detailed statistics about entities, relationships, and entity types
to help verify GraphRAG improvements.
"""

from django.core.management.base import BaseCommand
from ai_assistant.services.neo4j_service import get_neo4j_service
from ai_assistant.services.graph_builder import GraphBuilder
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Analyze the Neo4j knowledge graph and show detailed statistics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--entity-types',
            action='store_true',
            help='Show breakdown by entity type',
        )
        parser.add_argument(
            '--documents',
            action='store_true',
            help='Show document statistics',
        )
        parser.add_argument(
            '--relationships',
            action='store_true',
            help='Show relationship statistics',
        )
        parser.add_argument(
            '--top-entities',
            type=int,
            default=10,
            help='Show top N entities by occurrence (default: 10)',
        )
        parser.add_argument(
            '--document-id',
            type=int,
            help='Analyze specific document only',
        )

    def handle(self, *args, **options):
        show_entity_types = options.get('entity_types', False)
        show_documents = options.get('documents', False)
        show_relationships = options.get('relationships', False)
        top_n = options.get('top_entities', 10)
        document_id = options.get('document_id')

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('GraphRAG Graph Analysis'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')

        try:
            neo4j = get_neo4j_service()
            
            if not neo4j.test_connection():
                self.stdout.write(self.style.ERROR('❌ Cannot connect to Neo4j'))
                self.stdout.write('   Make sure Neo4j is running: docker ps | grep neo4j')
                return

            # Basic statistics
            stats = neo4j.get_graph_stats()
            
            self.stdout.write(self.style.SUCCESS('Basic Statistics:'))
            self.stdout.write(f'  Total nodes: {stats.get("total_nodes", 0)}')
            self.stdout.write(f'  Total relationships: {stats.get("total_relationships", 0)}')
            self.stdout.write('')

            # Node breakdown
            if stats.get('nodes'):
                self.stdout.write(self.style.SUCCESS('Node Breakdown:'))
                for node_info in stats['nodes']:
                    label = node_info.get('label', 'Unknown')
                    count = node_info.get('count', 0)
                    self.stdout.write(f'  {label}: {count}')
                self.stdout.write('')

            # Relationship breakdown
            if stats.get('relationships'):
                self.stdout.write(self.style.SUCCESS('Relationship Breakdown:'))
                for rel_info in stats['relationships']:
                    rel_type = rel_info.get('relationship_type', 'Unknown')
                    count = rel_info.get('count', 0)
                    self.stdout.write(f'  {rel_type}: {count}')
                self.stdout.write('')

            # Entity type breakdown (if requested or if showing all)
            if show_entity_types or (not show_documents and not show_relationships):
                self._show_entity_type_breakdown(neo4j, document_id)
                self.stdout.write('')

            # Top entities
            self._show_top_entities(neo4j, top_n, document_id)
            self.stdout.write('')

            # Document statistics
            if show_documents:
                self._show_document_stats(neo4j, document_id)
                self.stdout.write('')

            # Relationship statistics
            if show_relationships:
                self._show_relationship_stats(neo4j, document_id)
                self.stdout.write('')

            # Improvement indicators
            self._show_improvement_indicators(neo4j)
            self.stdout.write('')

        except Exception as e:
            logger.error(f"Error analyzing graph: {e}", exc_info=True)
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))

    def _show_entity_type_breakdown(self, neo4j, document_id=None):
        """Show breakdown of entities by type"""
        self.stdout.write(self.style.SUCCESS('Entity Type Breakdown:'))
        
        query = """
        MATCH (e:Entity)
        WHERE $doc_id IS NULL OR EXISTS {
            MATCH (d:Document {id: $doc_id})-[:CONTAINS]->(e)
        }
        RETURN e.type AS entity_type, 
               count(e) AS count,
               avg(e.confidence) AS avg_confidence
        ORDER BY count DESC
        """
        
        try:
            results = neo4j.execute_query(query, {'doc_id': str(document_id) if document_id else None})
            
            if not results:
                self.stdout.write('  No entities found')
                return
            
            # Group by entity type
            total = sum(r.get('count', 0) for r in results)
            
            # Enhanced entity types (from improvements)
            enhanced_types = ['CONCEPT', 'KEY_TERM', 'IMPORTANT_INFO', 'KEY_POINT', 'TOPIC', 'PROCEDURE']
            traditional_types = ['PRODUCT', 'ERROR_CODE', 'VERSION', 'SOFTWARE', 'PROBLEM', 'SOLUTION']
            
            enhanced_count = 0
            traditional_count = 0
            
            for result in results:
                entity_type = result.get('entity_type', 'UNKNOWN')
                count = result.get('count', 0)
                avg_conf = result.get('avg_confidence', 0)
                
                if entity_type in enhanced_types:
                    enhanced_count += count
                    indicator = '✨'  # Enhanced type
                elif entity_type in traditional_types:
                    traditional_count += count
                    indicator = '📌'  # Traditional type
                else:
                    indicator = '  '  # Other
                
                percentage = (count / total * 100) if total > 0 else 0
                self.stdout.write(
                    f'  {indicator} {entity_type:20} {count:6} ({percentage:5.1f}%) '
                    f'avg_conf: {avg_conf:.2f}' if avg_conf else ''
                )
            
            self.stdout.write('')
            self.stdout.write(f'  Enhanced types (✨): {enhanced_count} ({enhanced_count/total*100:.1f}%)' if total > 0 else '  Enhanced types (✨): 0')
            self.stdout.write(f'  Traditional types (📌): {traditional_count} ({traditional_count/total*100:.1f}%)' if total > 0 else '  Traditional types (📌): 0')
            
        except Exception as e:
            logger.error(f"Error getting entity type breakdown: {e}")
            self.stdout.write(self.style.ERROR(f'  Error: {str(e)}'))

    def _show_top_entities(self, neo4j, top_n, document_id=None):
        """Show top entities by occurrence"""
        self.stdout.write(self.style.SUCCESS(f'Top {top_n} Entities by Occurrence:'))
        
        query = """
        MATCH (e:Entity)
        WHERE $doc_id IS NULL OR EXISTS {
            MATCH (d:Document {id: $doc_id})-[:CONTAINS]->(e)
        }
        OPTIONAL MATCH (d:Document)-[:CONTAINS]->(e)
        WITH e, count(DISTINCT d) AS doc_count, count(d) AS total_occurrences
        RETURN e.name AS name,
               e.type AS type,
               e.normalized_name AS normalized,
               doc_count,
               total_occurrences,
               e.confidence AS confidence
        ORDER BY total_occurrences DESC, doc_count DESC
        LIMIT $top_n
        """
        
        try:
            results = neo4j.execute_query(query, {
                'doc_id': str(document_id) if document_id else None,
                'top_n': top_n
            })
            
            if not results:
                self.stdout.write('  No entities found')
                return
            
            for i, result in enumerate(results, 1):
                name = result.get('name', 'Unknown')[:40]  # Truncate long names
                entity_type = result.get('type', 'UNKNOWN')
                doc_count = result.get('doc_count', 0)
                occurrences = result.get('total_occurrences', 0)
                confidence = result.get('confidence', 0)
                
                # Indicator for enhanced types
                enhanced_types = ['CONCEPT', 'KEY_TERM', 'IMPORTANT_INFO', 'KEY_POINT']
                indicator = '✨' if entity_type in enhanced_types else '  '
                
                self.stdout.write(
                    f'  {i:2}. {indicator} {name:40} [{entity_type:15}] '
                    f'in {doc_count} docs, {occurrences} occurrences'
                    f' (conf: {confidence:.2f})' if confidence else ''
                )
                
        except Exception as e:
            logger.error(f"Error getting top entities: {e}")
            self.stdout.write(self.style.ERROR(f'  Error: {str(e)}'))

    def _show_document_stats(self, neo4j, document_id=None):
        """Show document statistics"""
        self.stdout.write(self.style.SUCCESS('Document Statistics:'))
        
        if document_id:
            query = """
            MATCH (d:Document {id: $doc_id})
            OPTIONAL MATCH (d)-[:CONTAINS]->(e:Entity)
            RETURN d.id AS id,
                   d.filename AS filename,
                   d.title AS title,
                   count(DISTINCT e) AS entity_count,
                   count(e) AS total_entity_occurrences
            """
            params = {'doc_id': str(document_id)}
        else:
            query = """
            MATCH (d:Document)
            OPTIONAL MATCH (d)-[:CONTAINS]->(e:Entity)
            RETURN d.id AS id,
                   d.filename AS filename,
                   d.title AS title,
                   count(DISTINCT e) AS entity_count,
                   count(e) AS total_entity_occurrences
            ORDER BY entity_count DESC
            LIMIT 20
            """
            params = {}
        
        try:
            results = neo4j.execute_query(query, params)
            
            if not results:
                self.stdout.write('  No documents found')
                return
            
            for result in results:
                doc_id = result.get('id', 'Unknown')
                filename = result.get('filename', 'Unknown')[:50]
                entity_count = result.get('entity_count', 0)
                occurrences = result.get('total_entity_occurrences', 0)
                
                self.stdout.write(
                    f'  ID {doc_id}: {filename:50} '
                    f'{entity_count} entities, {occurrences} occurrences'
                )
                
        except Exception as e:
            logger.error(f"Error getting document stats: {e}")
            self.stdout.write(self.style.ERROR(f'  Error: {str(e)}'))

    def _show_relationship_stats(self, neo4j, document_id=None):
        """Show relationship statistics"""
        self.stdout.write(self.style.SUCCESS('Relationship Statistics:'))
        
        query = """
        MATCH (e1:Entity)-[r:RELATED_TO]->(e2:Entity)
        WHERE $doc_id IS NULL OR EXISTS {
            MATCH (d:Document {id: $doc_id})-[:CONTAINS]->(e1)
        }
        RETURN e1.type AS type1,
               e2.type AS type2,
               count(r) AS count,
               avg(r.co_occurrence_count) AS avg_co_occurrence
        ORDER BY count DESC
        LIMIT 20
        """
        
        try:
            results = neo4j.execute_query(query, {
                'doc_id': str(document_id) if document_id else None
            })
            
            if not results:
                self.stdout.write('  No relationships found')
                return
            
            for result in results:
                type1 = result.get('type1', 'UNKNOWN')
                type2 = result.get('type2', 'UNKNOWN')
                count = result.get('count', 0)
                avg_co = result.get('avg_co_occurrence', 0)
                
                self.stdout.write(
                    f'  {type1:15} -> {type2:15} : {count:4} '
                    f'(avg co-occurrence: {avg_co:.1f})' if avg_co else ''
                )
                
        except Exception as e:
            logger.error(f"Error getting relationship stats: {e}")
            self.stdout.write(self.style.ERROR(f'  Error: {str(e)}'))

    def _show_improvement_indicators(self, neo4j):
        """Show indicators that improvements are working"""
        self.stdout.write(self.style.SUCCESS('Improvement Indicators:'))
        
        try:
            # Check for enhanced entity types
            enhanced_query = """
            MATCH (e:Entity)
            WHERE e.type IN ['CONCEPT', 'KEY_TERM', 'IMPORTANT_INFO', 'KEY_POINT', 'TOPIC', 'PROCEDURE']
            RETURN count(e) AS enhanced_count
            """
            
            enhanced_result = neo4j.execute_query(enhanced_query)
            enhanced_count = enhanced_result[0].get('enhanced_count', 0) if enhanced_result else 0
            
            # Check total entities
            total_query = "MATCH (e:Entity) RETURN count(e) AS total"
            total_result = neo4j.execute_query(total_query)
            total_count = total_result[0].get('total', 0) if total_result else 0
            
            # Calculate percentage
            if total_count > 0:
                enhanced_pct = (enhanced_count / total_count) * 100
                
                if enhanced_count > 0:
                    self.stdout.write(self.style.SUCCESS(
                        f'  ✅ Enhanced entity types found: {enhanced_count} ({enhanced_pct:.1f}%)'
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        '  ⚠️  No enhanced entity types found - documents may need reprocessing'
                    ))
                
                if enhanced_pct > 20:
                    self.stdout.write(self.style.SUCCESS(
                        '  ✅ Good coverage of enhanced entity types (>20%)'
                    ))
                elif enhanced_pct > 10:
                    self.stdout.write(self.style.WARNING(
                        '  ⚠️  Moderate coverage - consider reprocessing with LLM extraction'
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        '  ⚠️  Low coverage - reprocessing recommended'
                    ))
            else:
                self.stdout.write(self.style.WARNING('  ⚠️  No entities found in graph'))
            
            # Check for importance metadata
            importance_query = """
            MATCH (d:Document)-[r:CONTAINS]->(e:Entity)
            WHERE r.confidence > 0.8
            RETURN count(r) AS high_confidence_count
            """
            importance_result = neo4j.execute_query(importance_query)
            high_conf_count = importance_result[0].get('high_confidence_count', 0) if importance_result else 0
            
            if high_conf_count > 0:
                self.stdout.write(self.style.SUCCESS(
                    f'  ✅ High confidence entities: {high_conf_count}'
                ))
            
        except Exception as e:
            logger.error(f"Error checking improvement indicators: {e}")
            self.stdout.write(self.style.ERROR(f'  Error: {str(e)}'))

