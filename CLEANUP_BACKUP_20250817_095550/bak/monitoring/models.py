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
    
    class Meta:
        db_table = 'system_metrics'
        verbose_name = 'System Metric'
        verbose_name_plural = 'System Metrics'
        indexes = [
            models.Index(fields=['system', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.system.name} - {self.timestamp}"


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
