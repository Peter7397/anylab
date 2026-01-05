"""
Log Aggregation Setup Utilities

This module provides utilities and configuration examples for setting up
log aggregation systems (ELK stack, Loki, etc.) with the Django application.
"""

import logging
import os
from typing import Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class LogAggregationConfig:
    """Configuration helper for log aggregation systems"""
    
    @staticmethod
    def get_loki_config() -> Dict[str, Any]:
        """
        Get Loki configuration for log aggregation.
        Returns configuration dictionary for Grafana Loki.
        """
        return {
            'url': os.getenv('LOKI_URL', 'http://loki:3100'),
            'labels': {
                'job': 'anylab-backend',
                'environment': os.getenv('ENVIRONMENT', 'development'),
                'service': 'django',
            },
            'batch_size': int(os.getenv('LOKI_BATCH_SIZE', '100')),
            'timeout': int(os.getenv('LOKI_TIMEOUT', '10')),
            'enable_json_logging': os.getenv('ENABLE_JSON_LOGGING', 'False').lower() == 'true',
        }
    
    @staticmethod
    def get_elasticsearch_config() -> Dict[str, Any]:
        """
        Get Elasticsearch configuration for log aggregation.
        Returns configuration dictionary for ELK stack.
        """
        return {
            'hosts': os.getenv('ELASTICSEARCH_HOSTS', 'http://elasticsearch:9200').split(','),
            'index_name': os.getenv('ELASTICSEARCH_INDEX', 'anylab-logs'),
            'index_pattern': os.getenv('ELASTICSEARCH_INDEX_PATTERN', 'anylab-logs-*'),
            'username': os.getenv('ELASTICSEARCH_USERNAME', ''),
            'password': os.getenv('ELASTICSEARCH_PASSWORD', ''),
            'use_ssl': os.getenv('ELASTICSEARCH_USE_SSL', 'false').lower() == 'true',
            'verify_certs': os.getenv('ELASTICSEARCH_VERIFY_CERTS', 'true').lower() == 'true',
            'timeout': int(os.getenv('ELASTICSEARCH_TIMEOUT', '30')),
        }
    
    @staticmethod
    def get_fluentd_config() -> Dict[str, Any]:
        """
        Get Fluentd configuration for log aggregation.
        Returns configuration dictionary for Fluentd.
        """
        return {
            'host': os.getenv('FLUENTD_HOST', 'fluentd'),
            'port': int(os.getenv('FLUENTD_PORT', '24224')),
            'tag': os.getenv('FLUENTD_TAG', 'anylab.backend'),
            'timeout': int(os.getenv('FLUENTD_TIMEOUT', '60')),
            'buffer_size': int(os.getenv('FLUENTD_BUFFER_SIZE', '1048576')),  # 1MB
        }


def setup_log_aggregation_handler(aggregation_type: str = 'loki') -> Optional[logging.Handler]:
    """
    Set up a logging handler for the specified log aggregation system.
    
    Args:
        aggregation_type: Type of aggregation system ('loki', 'elasticsearch', 'fluentd')
    
    Returns:
        Configured logging handler or None if setup fails
    """
    try:
        if aggregation_type == 'loki':
            return _setup_loki_handler()
        elif aggregation_type == 'elasticsearch':
            return _setup_elasticsearch_handler()
        elif aggregation_type == 'fluentd':
            return _setup_fluentd_handler()
        else:
            logger.warning(f"Unknown aggregation type: {aggregation_type}")
            return None
    except Exception as e:
        logger.error(f"Failed to setup {aggregation_type} handler: {e}")
        return None


def _setup_loki_handler() -> Optional[logging.Handler]:
    """Set up Loki handler (requires python-logging-loki package)"""
    try:
        # Check if python-logging-loki is available
        try:
            from python_logging_loki import LokiHandler
        except ImportError:
            logger.warning("python-logging-loki not installed. Install with: pip install python-logging-loki")
            return None
        
        config = LogAggregationConfig.get_loki_config()
        
        handler = LokiHandler(
            url=config['url'],
            tags=config['labels'],
            version="1",
        )
        
        handler.setLevel(logging.INFO)
        logger.info(f"Loki handler configured: {config['url']}")
        return handler
        
    except Exception as e:
        logger.error(f"Failed to setup Loki handler: {e}")
        return None


def _setup_elasticsearch_handler() -> Optional[logging.Handler]:
    """Set up Elasticsearch handler (requires elasticsearch-logging package)"""
    try:
        # Check if elasticsearch handler is available
        try:
            from elasticsearch import Elasticsearch
            from elasticsearch_logging_handler import ElasticsearchHandler
        except ImportError:
            logger.warning("elasticsearch-logging-handler not installed. Install with: pip install elasticsearch-logging-handler")
            return None
        
        config = LogAggregationConfig.get_elasticsearch_config()
        
        es_client = Elasticsearch(
            hosts=config['hosts'],
            http_auth=(config['username'], config['password']) if config['username'] else None,
            use_ssl=config['use_ssl'],
            verify_certs=config['verify_certs'],
            timeout=config['timeout'],
        )
        
        handler = ElasticsearchHandler(
            es_client=es_client,
            index_name=config['index_name'],
        )
        
        handler.setLevel(logging.INFO)
        logger.info(f"Elasticsearch handler configured: {config['hosts']}")
        return handler
        
    except Exception as e:
        logger.error(f"Failed to setup Elasticsearch handler: {e}")
        return None


def _setup_fluentd_handler() -> Optional[logging.Handler]:
    """Set up Fluentd handler (requires fluent-logger package)"""
    try:
        # Check if fluent-logger is available
        try:
            from fluent import handler as fluent_handler
        except ImportError:
            logger.warning("fluent-logger not installed. Install with: pip install fluent-logger")
            return None
        
        config = LogAggregationConfig.get_fluentd_config()
        
        handler = fluent_handler.FluentHandler(
            config['tag'],
            host=config['host'],
            port=config['port'],
            buffer_size=config['buffer_size'],
        )
        
        handler.setLevel(logging.INFO)
        logger.info(f"Fluentd handler configured: {config['host']}:{config['port']}")
        return handler
        
    except Exception as e:
        logger.error(f"Failed to setup Fluentd handler: {e}")
        return None

