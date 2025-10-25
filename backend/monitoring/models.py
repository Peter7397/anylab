from django.db import models
from django.utils import timezone
from users.models import User


class System(models.Model):
    """System/PC information"""
    
    STATUS_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('maintenance', 'Maintenance'),
        ('error', 'Error'),
    ]
    
    name = models.CharField(max_length=200)
    hostname = models.CharField(max_length=200, unique=True)
    ip_address = models.GenericIPAddressField()
    mac_address = models.CharField(max_length=17, blank=True)
    os_type = models.CharField(max_length=50, blank=True)
    os_version = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offline')
    last_seen = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'systems'
        verbose_name = 'System'
        verbose_name_plural = 'Systems'
    
    def __str__(self):
        return f"{self.name} ({self.hostname})"


class SystemMetrics(models.Model):
    """System performance metrics"""
    
    system = models.ForeignKey(System, on_delete=models.CASCADE, related_name='metrics')
    timestamp = models.DateTimeField(auto_now_add=True)
    cpu_usage = models.FloatField()  # Percentage
    memory_usage = models.FloatField()  # Percentage
    disk_usage = models.FloatField()  # Percentage
    network_in = models.BigIntegerField()  # Bytes
    network_out = models.BigIntegerField()  # Bytes
    temperature = models.FloatField(null=True, blank=True)  # Celsius
    uptime = models.BigIntegerField()  # Seconds
    details = models.JSONField(default=dict, blank=True)  # Store detailed metrics from sysmon
    
    class Meta:
        db_table = 'system_metrics'
        verbose_name = 'System Metric'
        verbose_name_plural = 'System Metrics'
        indexes = [
            models.Index(fields=['system', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.system.name} - {self.timestamp}"
    
    @property
    def cpu_details(self):
        """Get detailed CPU information from sysmon data"""
        return self.details.get('cpu_details', {})
    
    @property
    def memory_details(self):
        """Get detailed memory information from sysmon data"""
        return self.details.get('memory_details', {})
    
    @property
    def disk_details(self):
        """Get detailed disk information from sysmon data"""
        return self.details.get('disk_details', {})
    
    @property
    def network_details(self):
        """Get detailed network information from sysmon data"""
        return self.details.get('network_details', {})


class LogEntry(models.Model):
    """System and application logs"""
    
    LEVEL_CHOICES = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    SOURCE_CHOICES = [
        ('system', 'System'),
        ('application', 'Application'),
        ('security', 'Security'),
        ('network', 'Network'),
        ('database', 'Database'),
    ]
    
    system = models.ForeignKey(System, on_delete=models.CASCADE, related_name='logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    message = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'log_entries'
        verbose_name = 'Log Entry'
        verbose_name_plural = 'Log Entries'
        indexes = [
            models.Index(fields=['system', 'timestamp']),
            models.Index(fields=['level', 'timestamp']),
            models.Index(fields=['source', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.system.name} - {self.level} - {self.timestamp}"


class Alert(models.Model):
    """System alerts and notifications"""
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    system = models.ForeignKey(System, on_delete=models.CASCADE, related_name='alerts')
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_alerts')
    
    class Meta:
        db_table = 'alerts'
        verbose_name = 'Alert'
        verbose_name_plural = 'Alerts'
        indexes = [
            models.Index(fields=['system', 'status']),
            models.Index(fields=['severity', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.system.name}"


class NetworkConnection(models.Model):
    """Network connection information"""
    
    STATUS_CHOICES = [
        ('established', 'Established'),
        ('listening', 'Listening'),
        ('time_wait', 'Time Wait'),
        ('close_wait', 'Close Wait'),
    ]
    
    system = models.ForeignKey(System, on_delete=models.CASCADE, related_name='connections')
    local_address = models.CharField(max_length=50)
    local_port = models.IntegerField()
    remote_address = models.CharField(max_length=50)
    remote_port = models.IntegerField()
    protocol = models.CharField(max_length=10)  # TCP, UDP
    status = models.CharField(max_length=15, choices=STATUS_CHOICES)
    process_name = models.CharField(max_length=200, blank=True)
    process_id = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'network_connections'
        verbose_name = 'Network Connection'
        verbose_name_plural = 'Network Connections'
        indexes = [
            models.Index(fields=['system', 'timestamp']),
            models.Index(fields=['protocol', 'status']),
        ]
    
    def __str__(self):
        return f"{self.system.name} - {self.local_address}:{self.local_port} -> {self.remote_address}:{self.remote_port}"


class DatabaseMetrics(models.Model):
    """Database performance metrics"""
    
    system = models.ForeignKey(System, on_delete=models.CASCADE, related_name='database_metrics')
    timestamp = models.DateTimeField(auto_now_add=True)
    active_connections = models.IntegerField()
    total_connections = models.IntegerField()
    slow_queries = models.IntegerField()
    query_time_avg = models.FloatField()  # Average query time in seconds
    cache_hit_ratio = models.FloatField()  # Percentage
    database_size = models.BigIntegerField()  # Bytes
    table_count = models.IntegerField()
    
    class Meta:
        db_table = 'database_metrics'
        verbose_name = 'Database Metric'
        verbose_name_plural = 'Database Metrics'
        indexes = [
            models.Index(fields=['system', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.system.name} - Database Metrics - {self.timestamp}"


class Application(models.Model):
    """Application information for monitoring"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
        ('maintenance', 'Maintenance'),
    ]
    
    AGENT_TYPE_CHOICES = [
        ('sysmon', 'SysMon Agent'),
        ('appmon', 'AppMon Agent'),
        ('windows', 'Windows Agent'),
        ('manual', 'Manual Entry'),
    ]
    
    name = models.CharField(max_length=200)
    system = models.ForeignKey(System, on_delete=models.CASCADE, related_name='applications')
    agent_type = models.CharField(max_length=20, choices=AGENT_TYPE_CHOICES, default='appmon')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    version = models.CharField(max_length=50, blank=True)
    last_seen = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    configuration = models.JSONField(default=dict, blank=True)  # AppMon config
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'applications'
        verbose_name = 'Application'
        verbose_name_plural = 'Applications'
        unique_together = ['name', 'system']
    
    def __str__(self):
        return f"{self.name} on {self.system.name}"


class ApplicationMetrics(models.Model):
    """Application monitoring metrics from AppMon agents"""
    
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='metrics')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # File monitoring metrics
    files_monitored = models.IntegerField(default=0)
    total_log_size_mb = models.FloatField(default=0.0)
    largest_file_mb = models.FloatField(default=0.0)
    
    # Alert metrics
    total_alerts_sent = models.IntegerField(default=0)
    unique_alerts_sent = models.IntegerField(default=0)
    duplicate_alerts_suppressed = models.IntegerField(default=0)
    
    # Performance metrics
    scan_duration_ms = models.FloatField(default=0.0)
    scan_frequency_per_minute = models.FloatField(default=0.0)
    
    # Source metrics
    active_sources = models.IntegerField(default=0)
    total_patterns = models.IntegerField(default=0)
    
    # Error metrics
    errors_count = models.IntegerField(default=0)
    last_error_time = models.DateTimeField(null=True, blank=True)
    
    # Cache metrics
    alert_cache_size = models.IntegerField(default=0)
    cache_hit_rate = models.FloatField(default=0.0)
    
    # Additional details
    details = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'application_metrics'
        verbose_name = 'Application Metric'
        verbose_name_plural = 'Application Metrics'
        indexes = [
            models.Index(fields=['application', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.application.name} - {self.timestamp}"


class ApplicationAlert(models.Model):
    """Application-specific alerts from AppMon agents"""
    
    SEVERITY_CHOICES = [
        ('critical', 'Critical'),
        ('error', 'Error'),
        ('warning', 'Warning'),
        ('info', 'Info'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='alerts')
    title = models.CharField(max_length=200)
    message = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    
    # AppMon specific fields
    source_name = models.CharField(max_length=100, blank=True)
    file_path = models.CharField(max_length=500, blank=True)
    line_number = models.IntegerField(null=True, blank=True)
    pattern_matched = models.CharField(max_length=100, blank=True)
    context_lines = models.JSONField(default=list, blank=True)
    fingerprint = models.CharField(max_length=64, blank=True)  # SHA256 hash
    
    # Standard alert fields
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_app_alerts')
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'application_alerts'
        verbose_name = 'Application Alert'
        verbose_name_plural = 'Application Alerts'
        indexes = [
            models.Index(fields=['application', 'status']),
            models.Index(fields=['severity', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['fingerprint']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.application.name}"
