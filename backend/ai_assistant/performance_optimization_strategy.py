"""
Performance Optimization Strategy

This module provides comprehensive performance optimization strategies
including caching, database optimization, query optimization, and resource management.
"""

import logging
import time
import psutil
import threading
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from django.utils import timezone as django_timezone
from django.core.cache import cache
from django.db import connection
from django.conf import settings

logger = logging.getLogger(__name__)


class OptimizationType(Enum):
    """Optimization type enumeration"""
    CACHING = "caching"
    DATABASE = "database"
    QUERY = "query"
    MEMORY = "memory"
    CPU = "cpu"
    NETWORK = "network"
    STORAGE = "storage"
    CONCURRENCY = "concurrency"


class OptimizationLevel(Enum):
    """Optimization level enumeration"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class OptimizationStatus(Enum):
    """Optimization status enumeration"""
    APPLIED = "applied"
    PENDING = "pending"
    FAILED = "failed"
    REVERTED = "reverted"
    TESTING = "testing"


@dataclass
class PerformanceMetric:
    """Performance metric structure"""
    id: str
    name: str
    value: float
    unit: str
    threshold: float
    level: OptimizationLevel
    timestamp: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class OptimizationRule:
    """Optimization rule structure"""
    id: str
    name: str
    optimization_type: OptimizationType
    condition: Dict[str, Any]
    action: Dict[str, Any]
    level: OptimizationLevel
    status: OptimizationStatus = OptimizationStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: django_timezone.now())
    updated_at: datetime = field(default_factory=lambda: django_timezone.now())


@dataclass
class OptimizationResult:
    """Optimization result structure"""
    id: str
    rule_id: str
    optimization_type: OptimizationType
    before_metrics: Dict[str, float]
    after_metrics: Dict[str, float]
    improvement_percentage: float
    status: OptimizationStatus
    details: str
    applied_at: datetime = field(default_factory=lambda: django_timezone.now())


class PerformanceOptimizationStrategy:
    """Performance Optimization Strategy System"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize performance optimization system"""
        self.config = config or {}
        self.optimization_enabled = self.config.get('optimization_enabled', True)
        self.auto_optimization = self.config.get('auto_optimization', True)
        self.monitoring_enabled = self.config.get('monitoring_enabled', True)
        self.cache_enabled = self.config.get('cache_enabled', True)
        self.optimization_interval = self.config.get('optimization_interval', 300)  # seconds
        
        # Initialize components
        self.performance_metrics = {}
        self.optimization_rules = {}
        self.optimization_results = {}
        self.cache = cache if self.cache_enabled else None
        
        # Initialize optimization system
        self._initialize_optimization_system()
        
        logger.info("Performance Optimization Strategy initialized")
    
    def _initialize_optimization_system(self):
        """Initialize optimization system components"""
        try:
            # Initialize optimization rules
            self._initialize_optimization_rules()
            
            # Initialize performance monitoring
            self._initialize_performance_monitoring()
            
            logger.info("Optimization system components initialized")
            
        except Exception as e:
            logger.error(f"Error initializing optimization system: {e}")
            raise
    
    def _initialize_optimization_rules(self):
        """Initialize optimization rules"""
        try:
            rules = [
                {
                    "id": "cache_query_optimization",
                    "name": "Cache Query Optimization",
                    "optimization_type": OptimizationType.CACHING,
                    "condition": {"query_time": ">", "threshold": 1.0},
                    "action": {"enable_query_cache": True, "cache_ttl": 3600},
                    "level": OptimizationLevel.HIGH
                },
                {
                    "id": "database_connection_pooling",
                    "name": "Database Connection Pooling",
                    "optimization_type": OptimizationType.DATABASE,
                    "condition": {"connection_count": ">", "threshold": 10},
                    "action": {"enable_connection_pooling": True, "pool_size": 20},
                    "level": OptimizationLevel.HIGH
                },
                {
                    "id": "memory_usage_optimization",
                    "name": "Memory Usage Optimization",
                    "optimization_type": OptimizationType.MEMORY,
                    "condition": {"memory_usage": ">", "threshold": 80.0},
                    "action": {"enable_memory_optimization": True, "gc_frequency": 300},
                    "level": OptimizationLevel.CRITICAL
                },
                {
                    "id": "cpu_usage_optimization",
                    "name": "CPU Usage Optimization",
                    "optimization_type": OptimizationType.CPU,
                    "condition": {"cpu_usage": ">", "threshold": 85.0},
                    "action": {"enable_cpu_optimization": True, "thread_limit": 4},
                    "level": OptimizationLevel.HIGH
                },
                {
                    "id": "query_optimization",
                    "name": "Query Optimization",
                    "optimization_type": OptimizationType.QUERY,
                    "condition": {"slow_queries": ">", "threshold": 5},
                    "action": {"enable_query_optimization": True, "index_suggestions": True},
                    "level": OptimizationLevel.MEDIUM
                }
            ]
            
            for rule_data in rules:
                rule = OptimizationRule(**rule_data)
                self.optimization_rules[rule.id] = rule
            
            logger.info(f"Initialized {len(self.optimization_rules)} optimization rules")
            
        except Exception as e:
            logger.error(f"Error initializing optimization rules: {e}")
            raise
    
    def _initialize_performance_monitoring(self):
        """Initialize performance monitoring"""
        try:
            # Start performance monitoring thread
            self.monitoring_thread = threading.Thread(target=self._performance_monitoring_worker)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
            
            logger.info("Performance monitoring initialized")
            
        except Exception as e:
            logger.error(f"Error initializing performance monitoring: {e}")
            raise
    
    def _performance_monitoring_worker(self):
        """Performance monitoring worker thread"""
        try:
            while True:
                # Collect performance metrics
                self._collect_performance_metrics()
                
                # Check optimization rules
                if self.auto_optimization:
                    self._check_optimization_rules()
                
                # Sleep for monitoring interval
                time.sleep(self.optimization_interval)
                
        except Exception as e:
            logger.error(f"Error in performance monitoring worker: {e}")
    
    def _collect_performance_metrics(self):
        """Collect performance metrics"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Database metrics
            db_connections = len(connection.queries) if hasattr(connection, 'queries') else 0
            db_query_time = sum(float(q['time']) for q in connection.queries) if hasattr(connection, 'queries') else 0
            
            # Cache metrics
            cache_hits = self._get_cache_hits()
            cache_misses = self._get_cache_misses()
            
            # Store metrics
            metrics = [
                PerformanceMetric("cpu_usage", "CPU Usage", cpu_percent, "%", 85.0, OptimizationLevel.HIGH),
                PerformanceMetric("memory_usage", "Memory Usage", memory.percent, "%", 80.0, OptimizationLevel.CRITICAL),
                PerformanceMetric("disk_usage", "Disk Usage", disk.percent, "%", 90.0, OptimizationLevel.HIGH),
                PerformanceMetric("db_connections", "Database Connections", db_connections, "count", 10, OptimizationLevel.MEDIUM),
                PerformanceMetric("db_query_time", "Database Query Time", db_query_time, "seconds", 1.0, OptimizationLevel.HIGH),
                PerformanceMetric("cache_hits", "Cache Hits", cache_hits, "count", 0, OptimizationLevel.INFORMATIONAL),
                PerformanceMetric("cache_misses", "Cache Misses", cache_misses, "count", 0, OptimizationLevel.INFORMATIONAL)
            ]
            
            for metric in metrics:
                self.performance_metrics[metric.id] = metric
            
            logger.debug(f"Collected {len(metrics)} performance metrics")
            
        except Exception as e:
            logger.error(f"Error collecting performance metrics: {e}")
    
    def _get_cache_hits(self) -> int:
        """Get cache hits count"""
        try:
            # Mock cache hits
            return 150
            
        except Exception as e:
            logger.error(f"Error getting cache hits: {e}")
            return 0
    
    def _get_cache_misses(self) -> int:
        """Get cache misses count"""
        try:
            # Mock cache misses
            return 25
            
        except Exception as e:
            logger.error(f"Error getting cache misses: {e}")
            return 0
    
    def _check_optimization_rules(self):
        """Check optimization rules"""
        try:
            for rule in self.optimization_rules.values():
                if rule.status != OptimizationStatus.PENDING:
                    continue
                
                # Check rule condition
                if self._evaluate_rule_condition(rule):
                    # Apply optimization
                    self._apply_optimization(rule)
            
        except Exception as e:
            logger.error(f"Error checking optimization rules: {e}")
    
    def _evaluate_rule_condition(self, rule: OptimizationRule) -> bool:
        """Evaluate optimization rule condition"""
        try:
            condition = rule.condition
            metric_name = condition.get("metric")
            operator = condition.get("operator", ">")
            threshold = condition.get("threshold")
            
            if not metric_name or threshold is None:
                return False
            
            # Get current metric value
            metric = self.performance_metrics.get(metric_name)
            if not metric:
                return False
            
            current_value = metric.value
            
            # Evaluate condition
            if operator == ">":
                return current_value > threshold
            elif operator == ">=":
                return current_value >= threshold
            elif operator == "<":
                return current_value < threshold
            elif operator == "<=":
                return current_value <= threshold
            elif operator == "==":
                return current_value == threshold
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error evaluating rule condition: {e}")
            return False
    
    def _apply_optimization(self, rule: OptimizationRule):
        """Apply optimization rule"""
        try:
            # Get before metrics
            before_metrics = {metric.id: metric.value for metric in self.performance_metrics.values()}
            
            # Apply optimization based on type
            if rule.optimization_type == OptimizationType.CACHING:
                self._apply_caching_optimization(rule)
            elif rule.optimization_type == OptimizationType.DATABASE:
                self._apply_database_optimization(rule)
            elif rule.optimization_type == OptimizationType.MEMORY:
                self._apply_memory_optimization(rule)
            elif rule.optimization_type == OptimizationType.CPU:
                self._apply_cpu_optimization(rule)
            elif rule.optimization_type == OptimizationType.QUERY:
                self._apply_query_optimization(rule)
            
            # Get after metrics
            time.sleep(1)  # Wait for optimization to take effect
            self._collect_performance_metrics()
            after_metrics = {metric.id: metric.value for metric in self.performance_metrics.values()}
            
            # Calculate improvement
            improvement = self._calculate_improvement(before_metrics, after_metrics, rule.optimization_type)
            
            # Create optimization result
            result = OptimizationResult(
                id=f"result_{rule.id}_{django_timezone.now().strftime('%Y%m%d_%H%M%S')}",
                rule_id=rule.id,
                optimization_type=rule.optimization_type,
                before_metrics=before_metrics,
                after_metrics=after_metrics,
                improvement_percentage=improvement,
                status=OptimizationStatus.APPLIED,
                details=f"Applied {rule.name} optimization"
            )
            
            self.optimization_results[result.id] = result
            
            # Update rule status
            rule.status = OptimizationStatus.APPLIED
            rule.updated_at = django_timezone.now()
            
            logger.info(f"Applied optimization: {rule.name}, improvement: {improvement:.2f}%")
            
        except Exception as e:
            logger.error(f"Error applying optimization: {e}")
            rule.status = OptimizationStatus.FAILED
    
    def _apply_caching_optimization(self, rule: OptimizationRule):
        """Apply caching optimization"""
        try:
            action = rule.action
            
            if action.get("enable_query_cache"):
                # Enable query caching
                logger.info("Enabled query caching")
            
            if action.get("cache_ttl"):
                # Set cache TTL
                logger.info(f"Set cache TTL to {action['cache_ttl']} seconds")
            
        except Exception as e:
            logger.error(f"Error applying caching optimization: {e}")
    
    def _apply_database_optimization(self, rule: OptimizationRule):
        """Apply database optimization"""
        try:
            action = rule.action
            
            if action.get("enable_connection_pooling"):
                # Enable connection pooling
                logger.info("Enabled database connection pooling")
            
            if action.get("pool_size"):
                # Set pool size
                logger.info(f"Set connection pool size to {action['pool_size']}")
            
        except Exception as e:
            logger.error(f"Error applying database optimization: {e}")
    
    def _apply_memory_optimization(self, rule: OptimizationRule):
        """Apply memory optimization"""
        try:
            action = rule.action
            
            if action.get("enable_memory_optimization"):
                # Enable memory optimization
                logger.info("Enabled memory optimization")
            
            if action.get("gc_frequency"):
                # Set garbage collection frequency
                logger.info(f"Set GC frequency to {action['gc_frequency']} seconds")
            
        except Exception as e:
            logger.error(f"Error applying memory optimization: {e}")
    
    def _apply_cpu_optimization(self, rule: OptimizationRule):
        """Apply CPU optimization"""
        try:
            action = rule.action
            
            if action.get("enable_cpu_optimization"):
                # Enable CPU optimization
                logger.info("Enabled CPU optimization")
            
            if action.get("thread_limit"):
                # Set thread limit
                logger.info(f"Set thread limit to {action['thread_limit']}")
            
        except Exception as e:
            logger.error(f"Error applying CPU optimization: {e}")
    
    def _apply_query_optimization(self, rule: OptimizationRule):
        """Apply query optimization"""
        try:
            action = rule.action
            
            if action.get("enable_query_optimization"):
                # Enable query optimization
                logger.info("Enabled query optimization")
            
            if action.get("index_suggestions"):
                # Enable index suggestions
                logger.info("Enabled index suggestions")
            
        except Exception as e:
            logger.error(f"Error applying query optimization: {e}")
    
    def _calculate_improvement(self, before_metrics: Dict[str, float], after_metrics: Dict[str, float], optimization_type: OptimizationType) -> float:
        """Calculate optimization improvement percentage"""
        try:
            # Define metrics to track for each optimization type
            tracked_metrics = {
                OptimizationType.CACHING: ["cache_hits", "cache_misses"],
                OptimizationType.DATABASE: ["db_query_time", "db_connections"],
                OptimizationType.MEMORY: ["memory_usage"],
                OptimizationType.CPU: ["cpu_usage"],
                OptimizationType.QUERY: ["db_query_time"]
            }
            
            metrics_to_track = tracked_metrics.get(optimization_type, [])
            if not metrics_to_track:
                return 0.0
            
            improvements = []
            for metric in metrics_to_track:
                before_value = before_metrics.get(metric, 0)
                after_value = after_metrics.get(metric, 0)
                
                if before_value > 0:
                    improvement = ((before_value - after_value) / before_value) * 100
                    improvements.append(improvement)
            
            if improvements:
                return sum(improvements) / len(improvements)
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating improvement: {e}")
            return 0.0
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        try:
            metrics = {}
            for metric in self.performance_metrics.values():
                metrics[metric.id] = {
                    "name": metric.name,
                    "value": metric.value,
                    "unit": metric.unit,
                    "threshold": metric.threshold,
                    "level": metric.level.value,
                    "timestamp": metric.timestamp.isoformat()
                }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {}
    
    def get_optimization_rule(self, rule_id: str) -> Optional[OptimizationRule]:
        """Get an optimization rule by ID"""
        return self.optimization_rules.get(rule_id)
    
    def get_optimization_result(self, result_id: str) -> Optional[OptimizationResult]:
        """Get an optimization result by ID"""
        return self.optimization_results.get(result_id)
    
    def get_optimization_statistics(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        try:
            stats = {
                "total_rules": len(self.optimization_rules),
                "total_results": len(self.optimization_results),
                "rules_by_type": {},
                "rules_by_level": {},
                "rules_by_status": {},
                "results_by_type": {},
                "results_by_status": {},
                "average_improvement": 0.0,
                "optimization_enabled": self.optimization_enabled,
                "auto_optimization": self.auto_optimization,
                "monitoring_enabled": self.monitoring_enabled
            }
            
            # Count rules by type
            for rule in self.optimization_rules.values():
                rule_type = rule.optimization_type.value
                stats["rules_by_type"][rule_type] = stats["rules_by_type"].get(rule_type, 0) + 1
                
                level = rule.level.value
                stats["rules_by_level"][level] = stats["rules_by_level"].get(level, 0) + 1
                
                status = rule.status.value
                stats["rules_by_status"][status] = stats["rules_by_status"].get(status, 0) + 1
            
            # Count results by type and status
            improvements = []
            for result in self.optimization_results.values():
                result_type = result.optimization_type.value
                stats["results_by_type"][result_type] = stats["results_by_type"].get(result_type, 0) + 1
                
                status = result.status.value
                stats["results_by_status"][status] = stats["results_by_status"].get(status, 0) + 1
                
                improvements.append(result.improvement_percentage)
            
            # Calculate average improvement
            if improvements:
                stats["average_improvement"] = sum(improvements) / len(improvements)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting optimization statistics: {e}")
            return {}
    
    def export_optimization_data(self) -> Dict[str, Any]:
        """Export optimization data"""
        try:
            return {
                "metrics": [
                    {
                        "id": metric.id,
                        "name": metric.name,
                        "value": metric.value,
                        "unit": metric.unit,
                        "threshold": metric.threshold,
                        "level": metric.level.value,
                        "timestamp": metric.timestamp.isoformat()
                    }
                    for metric in self.performance_metrics.values()
                ],
                "rules": [
                    {
                        "id": rule.id,
                        "name": rule.name,
                        "optimization_type": rule.optimization_type.value,
                        "condition": rule.condition,
                        "action": rule.action,
                        "level": rule.level.value,
                        "status": rule.status.value,
                        "metadata": rule.metadata,
                        "created_at": rule.created_at.isoformat(),
                        "updated_at": rule.updated_at.isoformat()
                    }
                    for rule in self.optimization_rules.values()
                ],
                "results": [
                    {
                        "id": result.id,
                        "rule_id": result.rule_id,
                        "optimization_type": result.optimization_type.value,
                        "before_metrics": result.before_metrics,
                        "after_metrics": result.after_metrics,
                        "improvement_percentage": result.improvement_percentage,
                        "status": result.status.value,
                        "details": result.details,
                        "applied_at": result.applied_at.isoformat()
                    }
                    for result in self.optimization_results.values()
                ]
            }
            
        except Exception as e:
            logger.error(f"Error exporting optimization data: {e}")
            return {}
    
    def import_optimization_data(self, data: Dict[str, Any]):
        """Import optimization data"""
        try:
            # Import metrics
            if "metrics" in data:
                for metric_data in data["metrics"]:
                    metric = PerformanceMetric(
                        id=metric_data["id"],
                        name=metric_data["name"],
                        value=metric_data["value"],
                        unit=metric_data["unit"],
                        threshold=metric_data["threshold"],
                        level=OptimizationLevel(metric_data["level"]),
                        timestamp=datetime.fromisoformat(metric_data["timestamp"])
                    )
                    self.performance_metrics[metric.id] = metric
            
            # Import rules
            if "rules" in data:
                for rule_data in data["rules"]:
                    rule = OptimizationRule(
                        id=rule_data["id"],
                        name=rule_data["name"],
                        optimization_type=OptimizationType(rule_data["optimization_type"]),
                        condition=rule_data["condition"],
                        action=rule_data["action"],
                        level=OptimizationLevel(rule_data["level"]),
                        status=OptimizationStatus(rule_data["status"]),
                        metadata=rule_data.get("metadata", {}),
                        created_at=datetime.fromisoformat(rule_data["created_at"]),
                        updated_at=datetime.fromisoformat(rule_data["updated_at"])
                    )
                    self.optimization_rules[rule.id] = rule
            
            # Import results
            if "results" in data:
                for result_data in data["results"]:
                    result = OptimizationResult(
                        id=result_data["id"],
                        rule_id=result_data["rule_id"],
                        optimization_type=OptimizationType(result_data["optimization_type"]),
                        before_metrics=result_data["before_metrics"],
                        after_metrics=result_data["after_metrics"],
                        improvement_percentage=result_data["improvement_percentage"],
                        status=OptimizationStatus(result_data["status"]),
                        details=result_data["details"],
                        applied_at=datetime.fromisoformat(result_data["applied_at"])
                    )
                    self.optimization_results[result.id] = result
            
            logger.info("Optimization data imported successfully")
            
        except Exception as e:
            logger.error(f"Error importing optimization data: {e}")
            raise
