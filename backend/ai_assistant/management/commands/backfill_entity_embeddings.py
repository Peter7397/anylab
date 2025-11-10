"""
Management command to backfill embeddings for existing entities in Neo4j

This command generates embeddings for entities that don't have them yet,
enabling semantic similarity search for GraphRAG.
"""

from django.core.management.base import BaseCommand
from ai_assistant.services.neo4j_service import get_neo4j_service
from ai_assistant.rag_service import EnhancedRAGService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Backfill embeddings for existing entities in Neo4j graph"

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of entities to process per batch (default: 10)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Maximum number of entities to process (default: all)'
        )
        parser.add_argument(
            '--similarity-threshold',
            type=float,
            default=0.6,
            help='Minimum similarity threshold for semantic search (default: 0.6)'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        limit = options.get('limit')
        similarity_threshold = options['similarity_threshold']
        
        neo4j = get_neo4j_service()
        rag_service = EnhancedRAGService()
        
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("Entity Embedding Backfill"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        
        # Get entities without embeddings
        query = """
        MATCH (e:Entity)
        WHERE e.embedding IS NULL
        RETURN e.id AS entity_id,
               e.name AS name,
               e.type AS type,
               e.normalized_name AS normalized_name
        ORDER BY e.occurrence_count DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        entities = neo4j.execute_query(query)
        
        total_entities = len(entities)
        if total_entities == 0:
            self.stdout.write(self.style.SUCCESS("✅ All entities already have embeddings!"))
            return
        
        self.stdout.write(f"\nFound {total_entities} entities without embeddings")
        self.stdout.write(f"Processing in batches of {batch_size}...\n")
        
        processed = 0
        failed = 0
        
        for i in range(0, total_entities, batch_size):
            batch = entities[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_entities + batch_size - 1) // batch_size
            
            self.stdout.write(f"\nProcessing batch {batch_num}/{total_batches} ({len(batch)} entities)...")
            
            for entity in batch:
                entity_id = entity.get('entity_id')
                entity_name = entity.get('name', 'Unknown')
                entity_type = entity.get('type', 'UNKNOWN')
                
                try:
                    # Generate embedding for entity
                    embedding_text = entity_name
                    if entity.get('normalized_name') and entity.get('normalized_name') != entity_name:
                        embedding_text = f"{entity_name} {entity.get('normalized_name')}"
                    
                    embedding = rag_service.get_embedding_from_ollama(embedding_text)
                    
                    # Update entity with embedding
                    update_query = """
                    MATCH (e:Entity {id: $entity_id})
                    SET e.embedding = $embedding
                    RETURN e.id AS id
                    """
                    
                    neo4j.execute_query(update_query, {
                        'entity_id': entity_id,
                        'embedding': embedding
                    })
                    
                    processed += 1
                    if processed % 10 == 0:
                        self.stdout.write(f"  ✓ Processed {processed}/{total_entities} entities...")
                    
                except Exception as e:
                    failed += 1
                    logger.error(f"Failed to generate embedding for entity {entity_id} ({entity_name}): {e}")
                    self.stdout.write(
                        self.style.WARNING(f"  ✗ Failed: {entity_name[:50]}... ({str(e)[:50]})")
                    )
                    continue
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(f"✅ Backfill complete!"))
        self.stdout.write(f"  Processed: {processed} entities")
        if failed > 0:
            self.stdout.write(self.style.WARNING(f"  Failed: {failed} entities"))
        self.stdout.write("=" * 60)
        
        # Show statistics
        stats_query = """
        MATCH (e:Entity)
        RETURN 
            count(e) AS total_entities,
            count(e.embedding) AS entities_with_embeddings,
            count(e) - count(e.embedding) AS entities_without_embeddings
        """
        stats = neo4j.execute_query(stats_query)
        if stats:
            stat = stats[0]
            total = stat.get('total_entities', 0)
            with_emb = stat.get('entities_with_embeddings', 0)
            without_emb = stat.get('entities_without_embeddings', 0)
            coverage = (with_emb / total * 100) if total > 0 else 0
            
            self.stdout.write(f"\n📊 Embedding Coverage:")
            self.stdout.write(f"  Total entities: {total}")
            self.stdout.write(f"  With embeddings: {with_emb} ({coverage:.1f}%)")
            self.stdout.write(f"  Without embeddings: {without_emb}")

