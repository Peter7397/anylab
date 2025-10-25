# AppMon Service Improvement Plan for OnLab Integration

## Overview
This document outlines the comprehensive improvements needed for the AppMon application monitoring service to better integrate with the OnLab monitoring system.

## Current AppMon Analysis

### ✅ Strengths:
- Multi-source log monitoring
- Pattern-based detection with regex
- Context-aware alerts
- Artifact collection
- File rotation handling
- Configurable sources

### 🔧 Areas for Improvement:
- Basic alert structure
- No deduplication
- Limited metrics
- Basic error handling
- No configuration validation
- No performance tracking

## High Priority Improvements (1-3)

### 1. Enhanced Alert Structure

**Current Alert (Basic):**
```python
alert = {
    "host": host,
    "service": "AppMonSvc", 
    "timestamp_utc": utcnow_iso(),
    "source": source.get("name","unknown"),
    "file": fp,
    "line_no": h["line_no"],
    "severity": h["severity"],
    "message": h["line"][:2000],
    "type": "log_match"
}
```

**Enhanced Alert (OnLab-Ready):**
```python
alert = {
    "host": self.host,
    "service": "AppMonSvc",
    "timestamp_utc": utcnow_iso(),
    "source": source.get("name","unknown"),
    "file": file_path,
    "line_no": hit["line_no"],
    "severity": hit["severity"],
    "message": hit["line"][:2000],
    "type": "log_match",
    
    # NEW FIELDS FOR ONELAB:
    "context": hit.get("context", []),  # Surrounding lines
    "fingerprint": fingerprint,  # For deduplication
    "version": "2.0.0",
    "application_name": source.get("name", "unknown"),
    "log_level": hit["severity"],
    "file_size_bytes": file_size,
    "file_modified_time": file_modified,
    "pattern_matched": pattern_name,
    "application_category": self.categorize_application(source.get("name")),
    "alert_id": f"appmon_{fingerprint[:16]}",
    
    "metadata": {
        "scan_cycle": self.stats.get("scan_cycles", 0),
        "total_files_scanned": self.stats.get("files_scanned", 0),
        "source_patterns_count": len(source.get("patterns", [])),
        "file_encoding": source.get("encoding", "utf-8")
    }
}
```

### 2. Deduplication System

**Key Features:**
- Configurable TTL (default: 5 minutes)
- Memory-efficient cache management
- Alert fingerprinting
- Statistics tracking

**Implementation:**
```python
class AppMonService:
    def __init__(self, config):
        # Deduplication system
        self.alert_cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.max_cache_size = 1000
        
        # Alert statistics
        self.alert_stats = {
            "total_alerts": 0,
            "duplicate_alerts": 0,
            "unique_alerts": 0
        }

    def is_duplicate_alert(self, alert_key):
        now = time.time()
        self.clean_alert_cache(now)
        
        if alert_key in self.alert_cache:
            if now - self.alert_cache[alert_key] < self.cache_ttl:
                self.alert_stats["duplicate_alerts"] += 1
                return True
            else:
                del self.alert_cache[alert_key]
        
        self.alert_cache[alert_key] = now
        self.alert_stats["unique_alerts"] += 1
        return False
```

### 3. Metrics Upload Feature

**Metrics Structure:**
```python
def collect_application_metrics(self):
    metrics = {
        "host": self.host,
        "service": "AppMonSvc",
        "timestamp_utc": utcnow_iso(),
        "version": "2.0.0",
        
        "metrics": {
            # File monitoring metrics
            "files_monitored": len(self.get_all_monitored_files()),
            "total_log_size_mb": self.get_total_log_size_mb(),
            "largest_file_mb": self.get_largest_file_mb(),
            
            # Alert metrics
            "total_alerts_sent": self.alert_stats["total_alerts"],
            "unique_alerts_sent": self.alert_stats["unique_alerts"],
            "duplicate_alerts_suppressed": self.alert_stats["duplicate_alerts"],
            
            # Performance metrics
            "last_scan_duration_ms": self.stats.get("last_scan_duration", 0) * 1000,
            "average_scan_duration_ms": self.get_average_scan_duration(),
            "scan_frequency_per_minute": 60.0 / self.interval,
            
            # Source metrics
            "active_sources": len(self.config.get("sources", [])),
            "total_patterns": self.get_total_patterns(),
            
            # Error metrics
            "errors_last_hour": self.stats.get("errors_count", 0),
            "last_error_time": self.stats.get("last_error_time"),
            
            # Cache metrics
            "alert_cache_size": len(self.alert_cache),
            "cache_hit_rate": self.get_cache_hit_rate()
        },
        
        # Application-specific metrics
        "applications": self.get_application_metrics()
    }
    
    return metrics
```

## Medium Priority Improvements (4-6)

### 4. Enhanced Error Handling & Logging

**Structured Logging:**
```python
class StructuredLogger:
    def log_scan_summary(self, cycle_stats, duration, errors=None):
        summary = {
            "event_type": "scan_summary",
            "timestamp": datetime.utcnow().isoformat(),
            "duration_seconds": round(duration, 2),
            "sources_processed": cycle_stats.get("sources_processed", 0),
            "files_scanned": cycle_stats.get("files_scanned", 0),
            "alerts_found": cycle_stats.get("total_alerts", 0),
            "errors_count": len(errors) if errors else 0,
            "status": "success" if not errors else "partial_failure"
        }
        
        if errors:
            summary["errors"] = errors
        
        self.logger.info(f"SCAN_SUMMARY: {json.dumps(summary)}")
```

### 5. Configuration Validation

**Comprehensive Validation:**
```python
class ConfigValidator:
    def validate_config(self, config):
        # Validate required fields
        self.validate_required_fields(config)
        
        # Validate paths
        self.validate_paths(config.get("paths", {}))
        
        # Validate alert server configuration
        self.validate_alert_server(config.get("alert_server", {}))
        
        # Validate sources
        self.validate_sources(config.get("sources", []))
        
        # Validate OnLab integration settings
        self.validate_onlab_integration(config.get("onlab_integration", {}))
        
        return len(self.errors) == 0
```

### 6. Performance Tracking

**Performance Monitoring:**
```python
class PerformanceTracker:
    def __init__(self, max_history=100):
        self.scan_durations = deque(maxlen=max_history)
        self.scan_stats = deque(maxlen=max_history)
        self.cpu_usage = deque(maxlen=max_history)
        self.memory_usage = deque(maxlen=max_history)
        self.files_per_second = deque(maxlen=max_history)
        self.bytes_per_second = deque(maxlen=max_history)
        self.alerts_per_second = deque(maxlen=max_history)
        self.error_rates = deque(maxlen=max_history)
        self.start_time = time.time()

    def get_performance_summary(self):
        return {
            "uptime_seconds": time.time() - self.start_time,
            "scan_performance": self.get_scan_performance(),
            "system_performance": self.get_system_performance(),
            "throughput_metrics": self.get_throughput_metrics(),
            "error_metrics": self.get_error_metrics()
        }
```

## Files to Create/Modify

### New Files:
1. `appmon_enhanced.py` - Main enhanced service
2. `structured_logger.py` - Enhanced logging
3. `config_validator.py` - Configuration validation
4. `performance_tracker.py` - Performance monitoring
5. `appmon.onlab.json` - OnLab-specific configuration

### Enhanced Configuration:
```json
{
  "scan_interval_sec": 30,
  "onlab_integration": {
    "upload_metrics": true,
    "metrics_interval_sec": 60,
    "application_mapping": {
      "AppA": "custom_application",
      "IIS": "web_server",
      "SQL": "database_server"
    },
    "alert_categories": {
      "critical": ["FATAL", "PANIC", "OutOfMemory"],
      "error": ["ERROR", "Exception"],
      "warning": ["WARN", "WARNING"]
    }
  },
  "alert_server": {
    "base_url": "http://localhost:8000/api/monitoring/appmon",
    "api_key": "CHANGE_ME_TO_ONELAB_API_KEY",
    "connect_timeout_sec": 5,
    "read_timeout_sec": 20
  }
}
```

## Integration with OnLab

### Backend API Endpoints:
- `/api/monitoring/appmon/alerts/` - Receive alerts
- `/api/monitoring/appmon/metrics/` - Receive metrics
- `/api/monitoring/appmon/agents/` - List agents
- `/api/monitoring/appmon/agents/{hostname}/` - Agent details

### Frontend Components:
- AppMon Agents dashboard
- Application-specific monitoring views
- Alert management interface
- Performance metrics visualization

## Implementation Priority

### Phase 1 (High Priority):
1. Enhanced alert structure
2. Deduplication system
3. Metrics upload feature

### Phase 2 (Medium Priority):
4. Enhanced error handling & logging
5. Configuration validation
6. Performance tracking

### Phase 3 (Low Priority):
7. Application categorization
8. Advanced health checks
9. Advanced features

## Benefits

### For OnLab Integration:
- Rich alert context for dashboard
- Comprehensive metrics for monitoring
- Reliable alert delivery with deduplication
- Performance insights for optimization

### For AppMon Service:
- Better reliability and error recovery
- Performance monitoring and optimization
- Enhanced configuration management
- Improved debugging and troubleshooting

## Next Steps

1. Implement Phase 1 improvements
2. Test integration with OnLab backend
3. Deploy enhanced AppMon agents
4. Monitor and optimize performance
5. Implement Phase 2 improvements
6. Add advanced features (Phase 3)

