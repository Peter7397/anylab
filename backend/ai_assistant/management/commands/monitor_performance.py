"""
Management command to monitor file processing performance.

Usage:
    python manage.py monitor_performance
    python manage.py monitor_performance --hours 48
"""

from django.core.management.base import BaseCommand
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta
from ai_assistant.models import UploadedFile, DocumentChunk
import psutil
import os
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Monitor file processing performance metrics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Time window in hours (default: 24)'
        )

    def handle(self, *args, **options):
        hours = options.get('hours', 24)
        cutoff_time = timezone.now() - timedelta(hours=hours)

        self.stdout.write(f'\n{"="*60}')
        self.stdout.write('PERFORMANCE MONITORING')
        self.stdout.write(f'{"="*60}')
        self.stdout.write(f'Time window: Last {hours} hours\n')

        # System resources
        self.stdout.write('System Resources:')
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        self.stdout.write(f'  CPU Usage: {cpu_percent:.1f}%')
        self.stdout.write(f'  Memory Usage: {memory.percent:.1f}% ({memory.used / (1024**3):.2f} GB / {memory.total / (1024**3):.2f} GB)')
        self.stdout.write(f'  Disk Usage: {disk.percent:.1f}% ({disk.used / (1024**3):.2f} GB / {disk.total / (1024**3):.2f} GB)')

        # Processing statistics
        self.stdout.write(f'\nProcessing Statistics:')
        
        files = UploadedFile.objects.filter(uploaded_at__gte=cutoff_time)
        total_files = files.count()
        
        if total_files == 0:
            self.stdout.write('  No files processed in this time window')
            return

        # File size statistics
        file_sizes = files.values_list('file_size', flat=True)
        if file_sizes:
            avg_size = sum(file_sizes) / len(file_sizes)
            max_size = max(file_sizes)
            min_size = min(file_sizes)
            
            self.stdout.write(f'\n  File Sizes:')
            self.stdout.write(f'    Average: {avg_size / (1024**2):.2f} MB')
            self.stdout.write(f'    Min: {min_size / (1024**2):.2f} MB')
            self.stdout.write(f'    Max: {max_size / (1024**2):.2f} MB')

        # Processing time (if we have timestamps)
        processed_files = files.filter(processing_status='ready')
        if processed_files.exists():
            # Calculate average processing time (rough estimate)
            processing_times = []
            for file in processed_files[:100]:  # Sample first 100
                if file.uploaded_at and hasattr(file, 'processed_at'):
                    # This would require a processed_at field
                    pass
            
            self.stdout.write(f'\n  Processing Status:')
            self.stdout.write(f'    Processed: {processed_files.count()}')
            self.stdout.write(f'    Failed: {files.filter(processing_status="failed").count()}')
            self.stdout.write(f'    Pending: {files.filter(processing_status="pending").count()}')

        # Chunk statistics
        chunks = DocumentChunk.objects.filter(
            uploaded_file__uploaded_at__gte=cutoff_time
        )
        total_chunks = chunks.count()
        
        if total_chunks > 0:
            self.stdout.write(f'\n  Chunk Statistics:')
            self.stdout.write(f'    Total chunks: {total_chunks}')
            
            # Average chunks per file
            chunks_per_file = chunks.values('uploaded_file').annotate(
                count=Count('id')
            ).aggregate(avg=Avg('count'))
            
            if chunks_per_file['avg']:
                self.stdout.write(f'    Average chunks per file: {chunks_per_file["avg"]:.1f}')

            # Embedding statistics
            chunks_with_embeddings = chunks.exclude(
                Q(embedding__isnull=True) | Q(embedding='[]')
            ).count()
            
            self.stdout.write(f'\n  Embedding Statistics:')
            self.stdout.write(f'    Chunks with embeddings: {chunks_with_embeddings}')
            self.stdout.write(f'    Chunks without embeddings: {total_chunks - chunks_with_embeddings}')
            
            if total_chunks > 0:
                embedding_rate = (chunks_with_embeddings / total_chunks) * 100
                self.stdout.write(f'    Embedding generation rate: {embedding_rate:.1f}%')

        # Throughput
        if total_files > 0:
            throughput = total_files / hours
            self.stdout.write(f'\n  Throughput:')
            self.stdout.write(f'    Files per hour: {throughput:.2f}')
            self.stdout.write(f'    Files per day: {throughput * 24:.2f}')

        self.stdout.write(f'\n{"="*60}\n')

