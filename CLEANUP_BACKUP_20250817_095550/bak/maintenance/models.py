from django.db import models
from django.utils import timezone
from users.models import User
from monitoring.models import System


class MaintenanceTask(models.Model):
    """Maintenance tasks and schedules"""
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('overdue', 'Overdue'),
    ]
    
    TASK_TYPE_CHOICES = [
        ('preventive', 'Preventive'),
        ('corrective', 'Corrective'),
        ('emergency', 'Emergency'),
        ('upgrade', 'Upgrade'),
        ('backup', 'Backup'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    
    # Scheduling
    scheduled_date = models.DateTimeField()
    estimated_duration = models.DurationField()  # Duration in hours
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    
    # Assignment
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    
    # Systems involved
    systems = models.ManyToManyField(System, related_name='maintenance_tasks')
    
    # Additional fields
    notes = models.TextField(blank=True)
    attachments = models.FileField(upload_to='maintenance_attachments/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'maintenance_tasks'
        verbose_name = 'Maintenance Task'
        verbose_name_plural = 'Maintenance Tasks'
        indexes = [
            models.Index(fields=['status', 'scheduled_date']),
            models.Index(fields=['priority', 'status']),
            models.Index(fields=['assigned_to', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    @property
    def is_overdue(self):
        return self.status == 'pending' and timezone.now() > self.scheduled_date


class MaintenanceSchedule(models.Model):
    """Recurring maintenance schedules"""
    
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    task_template = models.ForeignKey(MaintenanceTask, on_delete=models.CASCADE, related_name='schedules')
    frequency = models.CharField(max_length=15, choices=FREQUENCY_CHOICES)
    interval = models.IntegerField(default=1)  # Every X days/weeks/months
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'maintenance_schedules'
        verbose_name = 'Maintenance Schedule'
        verbose_name_plural = 'Maintenance Schedules'
    
    def __str__(self):
        return f"{self.name} - {self.get_frequency_display()}"


class SQLQuery(models.Model):
    """Database queries for monitoring and analysis"""
    
    QUERY_TYPE_CHOICES = [
        ('select', 'SELECT'),
        ('insert', 'INSERT'),
        ('update', 'UPDATE'),
        ('delete', 'DELETE'),
        ('ddl', 'DDL'),
        ('other', 'Other'),
    ]
    
    system = models.ForeignKey(System, on_delete=models.CASCADE, related_name='sql_queries')
    query_text = models.TextField()
    query_type = models.CharField(max_length=10, choices=QUERY_TYPE_CHOICES)
    execution_time = models.FloatField()  # Seconds
    rows_affected = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    application = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = 'sql_queries'
        verbose_name = 'SQL Query'
        verbose_name_plural = 'SQL Queries'
        indexes = [
            models.Index(fields=['system', 'timestamp']),
            models.Index(fields=['query_type', 'timestamp']),
            models.Index(fields=['execution_time']),
        ]
    
    def __str__(self):
        return f"{self.system.name} - {self.query_type} - {self.timestamp}"


class DatabaseBackup(models.Model):
    """Database backup records"""
    
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    system = models.ForeignKey(System, on_delete=models.CASCADE, related_name='backups')
    backup_name = models.CharField(max_length=200)
    backup_type = models.CharField(max_length=50)  # Full, Incremental, Differential
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField()  # Bytes
    status = models.CharField(max_length=15, choices=STATUS_CHOICES)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'database_backups'
        verbose_name = 'Database Backup'
        verbose_name_plural = 'Database Backups'
        indexes = [
            models.Index(fields=['system', 'started_at']),
            models.Index(fields=['status', 'started_at']),
        ]
    
    def __str__(self):
        return f"{self.backup_name} - {self.system.name}"


class PerformanceBaseline(models.Model):
    """Performance baselines for systems"""
    
    system = models.ForeignKey(System, on_delete=models.CASCADE, related_name='performance_baselines')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Baseline metrics
    cpu_baseline = models.FloatField()  # Average CPU usage
    memory_baseline = models.FloatField()  # Average memory usage
    disk_baseline = models.FloatField()  # Average disk usage
    network_baseline = models.FloatField()  # Average network usage
    
    # Thresholds
    cpu_threshold = models.FloatField()  # Alert threshold
    memory_threshold = models.FloatField()
    disk_threshold = models.FloatField()
    network_threshold = models.FloatField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'performance_baselines'
        verbose_name = 'Performance Baseline'
        verbose_name_plural = 'Performance Baselines'
    
    def __str__(self):
        return f"{self.name} - {self.system.name}"
