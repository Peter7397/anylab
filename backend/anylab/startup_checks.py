"""
Startup checks for required services
Verifies all Docker services (PostgreSQL, Redis, Neo4j) are accessible
"""
import logging
import time
from django.conf import settings

logger = logging.getLogger(__name__)


def check_neo4j_connection(max_retries=12, delay=5):
    """Check if Neo4j is accessible"""
    try:
        from ai_assistant.services.neo4j_service import get_neo4j_service
        neo4j = get_neo4j_service()
        
        for i in range(max_retries):
            try:
                if neo4j.test_connection():
                    logger.info("✅ Neo4j connection successful")
                    stats = neo4j.get_graph_stats()
                    logger.info(f"📊 Graph: {stats.get('nodes', 0)} nodes, {stats.get('relationships', 0)} relationships")
                    return True
            except Exception as e:
                logger.debug(f"Neo4j connection attempt {i+1}/{max_retries} failed: {e}")
            
            if i < max_retries - 1:
                logger.warning(f"⏳ Neo4j not ready yet (attempt {i+1}/{max_retries})...")
                time.sleep(delay)
        
        logger.warning("⚠️  Neo4j connection failed after retries - GraphRAG features may be unavailable")
        logger.warning("   Start Neo4j with: docker-compose up -d neo4j")
        return False
    except ImportError:
        logger.warning("⚠️  Neo4j service not available - GraphRAG features disabled")
        return False
    except Exception as e:
        logger.error(f"❌ Neo4j check failed: {e}")
        return False


def check_all_services():
    """Check all required services"""
    results = {
        'postgresql': False,
        'redis': False,
        'neo4j': False
    }
    
    # Check PostgreSQL
    try:
        from django.db import connection
        connection.ensure_connection()
        results['postgresql'] = True
        logger.info("✅ PostgreSQL connection successful")
    except Exception as e:
        logger.error(f"❌ PostgreSQL connection failed: {e}")
    
    # Check Redis
    try:
        from django.core.cache import cache
        cache.set('health_check', 'ok', 10)
        cache.get('health_check')
        results['redis'] = True
        logger.info("✅ Redis connection successful")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
    
    # Check Neo4j (non-blocking, logs warning if unavailable)
    results['neo4j'] = check_neo4j_connection(max_retries=3, delay=2)
    
    return results



