"""
Management command to perform pre-deployment checks.

Usage:
    python manage.py deployment_check
    python manage.py deployment_check --full
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from django.conf import settings
import sys
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Perform pre-deployment checks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--full',
            action='store_true',
            help='Run full check including tests'
        )

    def handle(self, *args, **options):
        full_check = options.get('full', False)
        
        self.stdout.write(f'\n{"="*60}')
        self.stdout.write('PRE-DEPLOYMENT CHECKS')
        self.stdout.write(f'{"="*60}\n')
        
        checks_passed = 0
        checks_failed = 0
        checks_warnings = 0
        
        # 1. Database connectivity
        self.stdout.write('1. Database Connectivity...')
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                self.stdout.write(self.style.SUCCESS('   ✓ Database connection OK'))
                checks_passed += 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ✗ Database connection failed: {e}'))
            checks_failed += 1
        
        # 2. Database migrations
        self.stdout.write('\n2. Database Migrations...')
        try:
            from django.db.migrations.executor import MigrationExecutor
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            if plan:
                self.stdout.write(self.style.WARNING(f'   ⚠ {len(plan)} unapplied migration(s)'))
                checks_warnings += 1
            else:
                self.stdout.write(self.style.SUCCESS('   ✓ All migrations applied'))
                checks_passed += 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ✗ Migration check failed: {e}'))
            checks_failed += 1
        
        # 3. pgvector extension
        self.stdout.write('\n3. pgvector Extension...')
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')")
                exists = cursor.fetchone()[0]
                if exists:
                    self.stdout.write(self.style.SUCCESS('   ✓ pgvector extension enabled'))
                    checks_passed += 1
                else:
                    self.stdout.write(self.style.ERROR('   ✗ pgvector extension not enabled'))
                    checks_failed += 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ✗ pgvector check failed: {e}'))
            checks_failed += 1
        
        # 4. Import checks
        self.stdout.write('\n4. Module Imports...')
        modules_to_check = [
            'ai_assistant.processors.metadata',
            'ai_assistant.processors.chunking',
            'ai_assistant.processors.ocr',
            'ai_assistant.processors.embeddings',
            'ai_assistant.tasks.file_processing_tasks',
            'ai_assistant.tasks.scraping_tasks',
            'ai_assistant.tasks.queue_tasks',
        ]
        
        import_errors = []
        for module_name in modules_to_check:
            try:
                __import__(module_name)
                self.stdout.write(f'   ✓ {module_name}')
                checks_passed += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ✗ {module_name}: {e}'))
                import_errors.append(f'{module_name}: {e}')
                checks_failed += 1
        
        # 5. Settings validation
        self.stdout.write('\n5. Settings Validation...')
        required_settings = [
            'DATABASES',
            'SECRET_KEY',
            'ALLOWED_HOSTS',
        ]
        
        for setting in required_settings:
            if hasattr(settings, setting):
                self.stdout.write(f'   ✓ {setting} configured')
                checks_passed += 1
            else:
                self.stdout.write(self.style.ERROR(f'   ✗ {setting} not configured'))
                checks_failed += 1
        
        # 6. Service connectivity (if full check)
        if full_check:
            self.stdout.write('\n6. Service Connectivity...')
            
            # Ollama
            try:
                import requests
                ollama_url = getattr(settings, 'OLLAMA_URL', 'http://localhost:11434')
                response = requests.get(f'{ollama_url}/api/tags', timeout=5)
                if response.status_code == 200:
                    self.stdout.write(self.style.SUCCESS('   ✓ Ollama service accessible'))
                    checks_passed += 1
                else:
                    self.stdout.write(self.style.WARNING(f'   ⚠ Ollama returned status {response.status_code}'))
                    checks_warnings += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   ⚠ Ollama not accessible: {e}'))
                checks_warnings += 1
            
            # Redis
            try:
                from django.core.cache import cache
                cache.set('deployment_check', 'ok', 10)
                if cache.get('deployment_check') == 'ok':
                    self.stdout.write(self.style.SUCCESS('   ✓ Redis cache working'))
                    checks_passed += 1
                else:
                    self.stdout.write(self.style.WARNING('   ⚠ Redis cache not working'))
                    checks_warnings += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   ⚠ Redis not accessible: {e}'))
                checks_warnings += 1
        
        # 7. Run tests (if full check)
        if full_check:
            self.stdout.write('\n7. Running Tests...')
            try:
                from io import StringIO
                test_output = StringIO()
                call_command('test', 'ai_assistant.tests.test_processors', 
                           verbosity=1, noinput=True, stdout=test_output, stderr=test_output)
                self.stdout.write(self.style.SUCCESS('   ✓ Processor tests passed'))
                checks_passed += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ✗ Tests failed: {e}'))
                checks_failed += 1
        
        # Summary
        self.stdout.write(f'\n{"="*60}')
        self.stdout.write('SUMMARY')
        self.stdout.write(f'{"="*60}')
        self.stdout.write(f'Passed: {checks_passed}')
        self.stdout.write(f'Failed: {checks_failed}')
        self.stdout.write(f'Warnings: {checks_warnings}')
        
        if checks_failed == 0:
            self.stdout.write(self.style.SUCCESS('\n✓ All critical checks passed! Ready for deployment.'))
            return 0
        else:
            self.stdout.write(self.style.ERROR(f'\n✗ {checks_failed} check(s) failed. Please fix before deployment.'))
            return 1

