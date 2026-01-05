"""
Management command to benchmark file processing performance.

Usage:
    python manage.py benchmark_performance
    python manage.py benchmark_performance --compare
"""

from django.core.management.base import BaseCommand
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.utils import timezone
from ai_assistant.models import UploadedFile, DocumentChunk
from ai_assistant.automatic_file_processor import automatic_file_processor
from django.core.files.storage import default_storage
import time
import psutil
import os
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Benchmark file processing performance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--compare',
            action='store_true',
            help='Compare with baseline metrics'
        )
        parser.add_argument(
            '--iterations',
            type=int,
            default=5,
            help='Number of test iterations (default: 5)'
        )

    def handle(self, *args, **options):
        compare = options.get('compare', False)
        iterations = options.get('iterations', 5)
        
        self.stdout.write(f'\n{"="*60}')
        self.stdout.write('PERFORMANCE BENCHMARKING')
        self.stdout.write(f'{"="*60}\n')
        
        # Get or create test user
        user, _ = User.objects.get_or_create(
            username='benchmark_user',
            defaults={'email': 'benchmark@example.com'}
        )
        
        # Create test PDF content
        pdf_content = b'%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 200 >>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Test PDF Content for Benchmarking) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000206 00000 n \ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n400\n%%EOF'
        
        results = {
            'processing_times': [],
            'memory_usage': [],
            'chunk_counts': [],
            'embedding_counts': [],
        }
        
        self.stdout.write(f'Running {iterations} iterations...\n')
        
        for i in range(iterations):
            self.stdout.write(f'Iteration {i+1}/{iterations}...')
            
            # Measure initial memory
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
            
            # Create test file
            filename = f'benchmark_test_{i}.pdf'
            uploaded_file = SimpleUploadedFile(
                name=filename,
                content=pdf_content,
                content_type='application/pdf'
            )
            
            # Create UploadedFile record
            uploaded_file_obj = UploadedFile.objects.create(
                user=user,
                filename=filename,
                file_size=len(pdf_content),
                file_hash=f'benchmark_hash_{i}',
                file_path=f'benchmark/{filename}',
                processing_status='pending'
            )
            
            # Save to storage
            file_path = default_storage.save(f'uploads/{filename}', uploaded_file)
            uploaded_file_obj.file_path = file_path
            uploaded_file_obj.save()
            
            try:
                # Measure processing time
                start_time = time.time()
                result = automatic_file_processor.process_file_fully(uploaded_file_obj.id)
                end_time = time.time()
                
                processing_time = end_time - start_time
                results['processing_times'].append(processing_time)
                
                # Measure final memory
                final_memory = process.memory_info().rss / (1024 * 1024)  # MB
                memory_delta = final_memory - initial_memory
                results['memory_usage'].append(memory_delta)
                
                # Get chunk and embedding counts
                uploaded_file_obj.refresh_from_db()
                chunk_count = DocumentChunk.objects.filter(
                    uploaded_file=uploaded_file_obj
                ).count()
                results['chunk_counts'].append(chunk_count)
                results['embedding_counts'].append(result.get('embedding_count', 0))
                
                self.stdout.write(f'  Time: {processing_time:.2f}s, Memory: {memory_delta:.2f}MB, Chunks: {chunk_count}')
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Failed: {e}'))
            finally:
                # Cleanup
                try:
                    if default_storage.exists(file_path):
                        default_storage.delete(file_path)
                    uploaded_file_obj.delete()
                except Exception:
                    pass
        
        # Calculate statistics
        self.stdout.write(f'\n{"="*60}')
        self.stdout.write('BENCHMARK RESULTS')
        self.stdout.write(f'{"="*60}\n')
        
        if results['processing_times']:
            avg_time = sum(results['processing_times']) / len(results['processing_times'])
            min_time = min(results['processing_times'])
            max_time = max(results['processing_times'])
            
            self.stdout.write('Processing Time:')
            self.stdout.write(f'  Average: {avg_time:.2f}s')
            self.stdout.write(f'  Min: {min_time:.2f}s')
            self.stdout.write(f'  Max: {max_time:.2f}s')
        
        if results['memory_usage']:
            avg_memory = sum(results['memory_usage']) / len(results['memory_usage'])
            max_memory = max(results['memory_usage'])
            
            self.stdout.write('\nMemory Usage:')
            self.stdout.write(f'  Average: {avg_memory:.2f}MB')
            self.stdout.write(f'  Peak: {max_memory:.2f}MB')
        
        if results['chunk_counts']:
            avg_chunks = sum(results['chunk_counts']) / len(results['chunk_counts'])
            
            self.stdout.write('\nChunk Generation:')
            self.stdout.write(f'  Average chunks per file: {avg_chunks:.1f}')
        
        if results['embedding_counts']:
            avg_embeddings = sum(results['embedding_counts']) / len(results['embedding_counts'])
            
            self.stdout.write('\nEmbedding Generation:')
            self.stdout.write(f'  Average embeddings per file: {avg_embeddings:.1f}')
        
        # System resources
        self.stdout.write('\nSystem Resources:')
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        self.stdout.write(f'  CPU Usage: {cpu_percent:.1f}%')
        self.stdout.write(f'  Memory Usage: {memory.percent:.1f}%')
        
        self.stdout.write(f'\n{"="*60}\n')
        
        # Save baseline if compare mode
        if compare:
            self.stdout.write('Note: Use --compare to compare with previous baseline')
        
        return results

