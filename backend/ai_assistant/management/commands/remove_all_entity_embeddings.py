"""
Management command to remove all entity embeddings from Neo4j

This command removes the 'embedding' property from all Entity nodes in Neo4j.
Useful for cleaning up orphaned embeddings after files are deleted.
"""

from django.core.management.base import BaseCommand
from ai_assistant.service_classes.neo4j_service import get_neo4j_service
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Remove all entity embeddings from Neo4j'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be removed without actually removing',
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm removal (required for actual deletion)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        confirm = options['confirm']
        
        # Use existing Neo4j service
        self.stdout.write("Connecting to Neo4j...")
        
        try:
            neo4j_service = get_neo4j_service()
            
            if not neo4j_service or not neo4j_service.driver:
                self.stdout.write(self.style.ERROR("Failed to connect to Neo4j"))
                return
            
            # Count entities with embeddings
            query = 'MATCH (e:Entity) WHERE e.embedding IS NOT NULL RETURN count(e) as count'
            results = neo4j_service.execute_query(query)
            count_with_embeddings = results[0]['count'] if results else 0
            
            # Count total entities
            query = 'MATCH (e:Entity) RETURN count(e) as count'
            results = neo4j_service.execute_query(query)
            total_entities = results[0]['count'] if results else 0
            
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"Entity Embeddings Summary:")
            self.stdout.write(f"  Total entities: {total_entities}")
            self.stdout.write(f"  Entities with embeddings: {count_with_embeddings}")
            self.stdout.write(f"{'='*60}\n")
            
            if count_with_embeddings == 0:
                self.stdout.write(self.style.SUCCESS("No entity embeddings found. Nothing to remove."))
                return
            
            if dry_run:
                self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
                self.stdout.write(f"Would remove embeddings from {count_with_embeddings} entities")
                return
            
            if not confirm:
                self.stdout.write(self.style.ERROR("ERROR: --confirm flag is required to remove embeddings"))
                self.stdout.write("Run with: python manage.py remove_all_entity_embeddings --confirm")
                return
            
            # Remove all embeddings
            self.stdout.write(f"Removing embeddings from {count_with_embeddings} entities...")
            
            # Use execute_query to get count, then remove
            query = """
            MATCH (e:Entity)
            WHERE e.embedding IS NOT NULL
            REMOVE e.embedding
            RETURN count(e) as removed
            """
            
            # Execute and get result
            results = neo4j_service.execute_query(query)
            removed_count = results[0]['removed'] if results else 0
            
            if removed_count == 0:
                self.stdout.write(self.style.WARNING("No embeddings were removed"))
                return
            
            # Verify removal
            query = 'MATCH (e:Entity) WHERE e.embedding IS NOT NULL RETURN count(e) as count'
            results = neo4j_service.execute_query(query)
            remaining = results[0]['count'] if results else 0
            
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(self.style.SUCCESS(f"✓ Successfully removed embeddings from {removed_count} entities"))
            self.stdout.write(f"  Remaining entities with embeddings: {remaining}")
            self.stdout.write(f"{'='*60}\n")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
            logger.error(f"Error removing entity embeddings: {e}", exc_info=True)
            raise
