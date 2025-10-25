from rest_framework import serializers
from .models import System, SystemMetrics, Alert, LogEntry, NetworkConnection, DatabaseMetrics, Application, ApplicationMetrics, ApplicationAlert

class SystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = System
        fields = '__all__'

class SystemMetricsSerializer(serializers.ModelSerializer):
    system_name = serializers.CharField(source='system.name', read_only=True)
    
    class Meta:
        model = SystemMetrics
        fields = '__all__'

class AlertSerializer(serializers.ModelSerializer):
    system_name = serializers.CharField(source='system.name', read_only=True)
    acknowledged_by_name = serializers.CharField(source='acknowledged_by.username', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.username', read_only=True)
    
    class Meta:
        model = Alert
        fields = '__all__'

class LogEntrySerializer(serializers.ModelSerializer):
    system_name = serializers.CharField(source='system.name', read_only=True)
    
    class Meta:
        model = LogEntry
        fields = '__all__'

class NetworkConnectionSerializer(serializers.ModelSerializer):
    system_name = serializers.CharField(source='system.name', read_only=True)
    
    class Meta:
        model = NetworkConnection
        fields = '__all__'

class DatabaseMetricsSerializer(serializers.ModelSerializer):
    system_name = serializers.CharField(source='system.name', read_only=True)
    
    class Meta:
        model = DatabaseMetrics
        fields = '__all__'


class ApplicationSerializer(serializers.ModelSerializer):
    system_name = serializers.CharField(source='system.name', read_only=True)
    system_hostname = serializers.CharField(source='system.hostname', read_only=True)
    
    class Meta:
        model = Application
        fields = '__all__'


class ApplicationMetricsSerializer(serializers.ModelSerializer):
    application_name = serializers.CharField(source='application.name', read_only=True)
    system_name = serializers.CharField(source='application.system.name', read_only=True)
    
    class Meta:
        model = ApplicationMetrics
        fields = '__all__'


class ApplicationAlertSerializer(serializers.ModelSerializer):
    application_name = serializers.CharField(source='application.name', read_only=True)
    system_name = serializers.CharField(source='application.system.name', read_only=True)
    acknowledged_by_name = serializers.CharField(source='acknowledged_by.username', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.username', read_only=True)
    
    class Meta:
        model = ApplicationAlert
        fields = '__all__'
