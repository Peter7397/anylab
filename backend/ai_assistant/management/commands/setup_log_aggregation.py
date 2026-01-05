"""
Django management command to set up log aggregation.

This command provides instructions and configuration for setting up
log aggregation systems (Loki, ELK stack, etc.).
"""

import logging
import os
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Provides instructions and setup for log aggregation systems.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--system',
            type=str,
            choices=['loki', 'elk', 'fluentd'],
            default='loki',
            help='Log aggregation system to set up (default: loki)'
        )
        parser.add_argument(
            '--check',
            action='store_true',
            help='Check if log aggregation is properly configured'
        )

    def handle(self, *args, **options):
        system = options['system']
        check = options['check']

        if check:
            self._check_configuration(system)
        else:
            self._show_setup_instructions(system)

    def _check_configuration(self, system: str):
        """Check if log aggregation is properly configured"""
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("LOG AGGREGATION CONFIGURATION CHECK"))
        self.stdout.write(self.style.SUCCESS("=" * 60))

        if system == 'loki':
            self._check_loki_config()
        elif system == 'elk':
            self._check_elk_config()
        elif system == 'fluentd':
            self._check_fluentd_config()

    def _check_loki_config(self):
        """Check Loki configuration"""
        loki_url = os.getenv('LOKI_URL', 'http://loki:3100')
        json_logging = os.getenv('ENABLE_JSON_LOGGING', 'False').lower() == 'true'

        self.stdout.write(f"\nLoki Configuration:")
        self.stdout.write(f"  URL: {loki_url}")
        self.stdout.write(f"  JSON Logging: {'Enabled' if json_logging else 'Disabled'}")

        # Check if JSON logging is enabled in settings
        if hasattr(settings, 'LOGGING'):
            handlers = settings.LOGGING.get('handlers', {})
            if 'json_file' in handlers:
                self.stdout.write(self.style.SUCCESS("  ✓ JSON logging handler configured"))
            else:
                self.stdout.write(self.style.WARNING("  ⚠ JSON logging handler not found in settings"))

        # Check if logs directory exists
        logs_dir = os.path.join(settings.BASE_DIR, 'logs')
        if os.path.exists(logs_dir):
            self.stdout.write(self.style.SUCCESS(f"  ✓ Logs directory exists: {logs_dir}"))
        else:
            self.stdout.write(self.style.WARNING(f"  ⚠ Logs directory not found: {logs_dir}"))

    def _check_elk_config(self):
        """Check ELK stack configuration"""
        es_hosts = os.getenv('ELASTICSEARCH_HOSTS', 'http://elasticsearch:9200')
        self.stdout.write(f"\nElasticsearch Configuration:")
        self.stdout.write(f"  Hosts: {es_hosts}")

    def _check_fluentd_config(self):
        """Check Fluentd configuration"""
        fluentd_host = os.getenv('FLUENTD_HOST', 'fluentd')
        fluentd_port = os.getenv('FLUENTD_PORT', '24224')
        self.stdout.write(f"\nFluentd Configuration:")
        self.stdout.write(f"  Host: {fluentd_host}:{fluentd_port}")

    def _show_setup_instructions(self, system: str):
        """Show setup instructions for the specified system"""
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS(f"LOG AGGREGATION SETUP: {system.upper()}"))
        self.stdout.write(self.style.SUCCESS("=" * 60))

        if system == 'loki':
            self._show_loki_instructions()
        elif system == 'elk':
            self._show_elk_instructions()
        elif system == 'fluentd':
            self._show_fluentd_instructions()

    def _show_loki_instructions(self):
        """Show Loki setup instructions"""
        self.stdout.write("""
1. Start Loki stack using Docker Compose:
   docker-compose -f docker-compose.logging.yml up -d loki promtail grafana

2. Enable JSON logging in Django settings:
   Set ENABLE_JSON_LOGGING=true in your .env file

3. Configure Loki URL (optional, defaults to http://loki:3100):
   Set LOKI_URL=http://your-loki-host:3100 in your .env file

4. Access Grafana dashboard:
   http://localhost:3000
   Default credentials: admin/admin

5. Import pre-configured dashboards from:
   docker/grafana-dashboards/

6. Verify logs are being collected:
   python manage.py setup_log_aggregation --system loki --check
""")

    def _show_elk_instructions(self):
        """Show ELK stack setup instructions"""
        self.stdout.write("""
1. Start ELK stack using Docker Compose:
   docker-compose -f docker-compose.logging.yml up -d elasticsearch logstash kibana

2. Configure Elasticsearch connection:
   Set ELASTICSEARCH_HOSTS=http://elasticsearch:9200 in your .env file

3. Enable JSON logging in Django settings:
   Set ENABLE_JSON_LOGGING=true in your .env file

4. Access Kibana dashboard:
   http://localhost:5601

5. Create index pattern in Kibana:
   - Go to Management > Index Patterns
   - Create pattern: anylab-logs-*

6. Verify logs are being collected:
   python manage.py setup_log_aggregation --system elk --check
""")

    def _show_fluentd_instructions(self):
        """Show Fluentd setup instructions"""
        self.stdout.write("""
1. Install fluent-logger Python package:
   pip install fluent-logger

2. Configure Fluentd connection:
   Set FLUENTD_HOST=your-fluentd-host in your .env file
   Set FLUENTD_PORT=24224 in your .env file

3. Enable JSON logging in Django settings:
   Set ENABLE_JSON_LOGGING=true in your .env file

4. Verify logs are being collected:
   python manage.py setup_log_aggregation --system fluentd --check
""")

