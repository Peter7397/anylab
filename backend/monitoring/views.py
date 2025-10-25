from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import json
import logging
from .models import System, SystemMetrics, Alert, LogEntry, Application, ApplicationMetrics, ApplicationAlert
from .serializers import SystemSerializer, SystemMetricsSerializer, AlertSerializer, ApplicationSerializer, ApplicationMetricsSerializer, ApplicationAlertSerializer

logger = logging.getLogger(__name__)

# Create your views here.

@api_view(['GET'])
def system_list(request):
    """Placeholder view for system list"""
    return Response({'message': 'System list endpoint - coming soon'})

@csrf_exempt
@require_http_methods(["POST"])
def sysmon_alert_endpoint(request):
    """
    Endpoint to receive alerts from sysmon agents
    """
    try:
        data = json.loads(request.body)
        logger.info(f"Received sysmon alert: {data}")
        
        # Extract alert data
        host = data.get('host')
        service = data.get('service', 'SysMonSvc')
        timestamp_utc = data.get('timestamp_utc')
        severity = data.get('severity', 'warning')
        metric = data.get('metric')
        value = data.get('value')
        threshold = data.get('threshold')
        dimensions = data.get('dimensions', {})
        fingerprint = data.get('fingerprint')
        
        # Get or create system
        system, created = System.objects.get_or_create(
            hostname=host,
            defaults={
                'name': host,
                'ip_address': request.META.get('REMOTE_ADDR', '0.0.0.0'),
                'status': 'online',
                'last_seen': timezone.now()
            }
        )
        
        if not created:
            system.last_seen = timezone.now()
            system.save()
        
        # Create alert
        alert = Alert.objects.create(
            title=f"{metric} Alert - {host}",
            description=f"{metric}: {value} (threshold: {threshold})",
            system=system,
            severity=severity,
            status='active'
        )
        
        # Create log entry
        LogEntry.objects.create(
            system=system,
            level='WARNING' if severity == 'warning' else 'ERROR',
            source='system',
            message=f"{metric} threshold exceeded: {value} > {threshold}",
            details={
                'metric': metric,
                'value': value,
                'threshold': threshold,
                'dimensions': dimensions,
                'fingerprint': fingerprint,
                'service': service
            },
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return JsonResponse({'status': 'success', 'alert_id': alert.id})
        
    except Exception as e:
        logger.error(f"Error processing sysmon alert: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def sysmon_metrics_endpoint(request):
    """
    Endpoint to receive system metrics from sysmon agents
    """
    try:
        data = json.loads(request.body)
        logger.info(f"Received sysmon metrics from {data.get('host', 'unknown')}")
        
        host = data.get('host')
        metrics_data = data.get('metrics', {})
        timestamp_utc = data.get('timestamp_utc')
        agent_version = data.get('agent_version', '1.0.0')
        agent_stats = data.get('agent_stats', {})
        
        # Get or create system
        system, created = System.objects.get_or_create(
            hostname=host,
            defaults={
                'name': host,
                'ip_address': request.META.get('REMOTE_ADDR', '0.0.0.0'),
                'status': 'online',
                'last_seen': timezone.now()
            }
        )
        
        if not created:
            system.last_seen = timezone.now()
            system.save()
        
        # Extract detailed metrics
        cpu_data = metrics_data.get('cpu', {})
        mem_data = metrics_data.get('mem', {})
        disk_data = metrics_data.get('disk', {})
        net_data = metrics_data.get('net', {})
        sys_data = metrics_data.get('system', {})
        
        # Calculate aggregate disk usage
        total_disk_usage = 0.0
        disk_count = 0
        if disk_data.get('disks'):
            for disk in disk_data['disks']:
                if disk.get('used_pct') is not None:
                    total_disk_usage += disk['used_pct']
                    disk_count += 1
            if disk_count > 0:
                total_disk_usage = total_disk_usage / disk_count
        
        # Calculate aggregate network usage
        total_network_in = 0
        total_network_out = 0
        if net_data.get('stats'):
            for nic_stats in net_data['stats'].values():
                total_network_in += nic_stats.get('rx_Bps', 0)
                total_network_out += nic_stats.get('tx_Bps', 0)
        
        # Create system metrics with enhanced data
        system_metrics = SystemMetrics.objects.create(
            system=system,
            cpu_usage=cpu_data.get('cpu_total_pct', 0.0),
            memory_usage=mem_data.get('ram_used_pct', 0.0),
            disk_usage=total_disk_usage,
            network_in=int(total_network_in),
            network_out=int(total_network_out),
            uptime=sys_data.get('uptime_seconds', 0),
            temperature=None,  # Will be added if available in future
            details={
                'cpu_details': cpu_data,
                'memory_details': mem_data,
                'disk_details': disk_data,
                'network_details': net_data,
                'system_details': sys_data,
                'agent_version': agent_version,
                'agent_stats': agent_stats,
                'collection_time_ms': metrics_data.get('collection_time_ms', 0),
                'raw_metrics': metrics_data
            }
        )
        
        # Update system information if we have new data
        if sys_data.get('uptime_seconds'):
            # This could be used to update system status or other fields
            pass
        
        return JsonResponse({
            'status': 'success', 
            'metrics_id': system_metrics.id,
            'message': f'Processed metrics for {host}'
        })
        
    except Exception as e:
        logger.error(f"Error processing sysmon metrics: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sysmon_agents_list(request):
    """
    List all sysmon agents and their status
    """
    systems = System.objects.filter(hostname__isnull=False).order_by('-last_seen')
    serializer = SystemSerializer(systems, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sysmon_agent_detail(request, hostname):
    """
    Get detailed information about a specific sysmon agent
    """
    try:
        system = System.objects.get(hostname=hostname)
        serializer = SystemSerializer(system)
        return Response(serializer.data)
    except System.DoesNotExist:
        return Response({'error': 'System not found'}, status=404)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sysmon_agent_metrics(request, hostname):
    """
    Get metrics history for a specific sysmon agent
    """
    try:
        system = System.objects.get(hostname=hostname)
        metrics = SystemMetrics.objects.filter(system=system).order_by('-timestamp')[:100]
        serializer = SystemMetricsSerializer(metrics, many=True)
        return Response(serializer.data)
    except System.DoesNotExist:
        return Response({'error': 'System not found'}, status=404)


# AppMon Agent Endpoints
@csrf_exempt
@require_http_methods(["POST"])
def appmon_alert_endpoint(request):
    """
    Endpoint to receive alerts from AppMon agents
    """
    try:
        data = json.loads(request.body)
        logger.info(f"Received AppMon alert: {data}")
        
        # Extract alert data
        host = data.get('host')
        service = data.get('service', 'AppMonSvc')
        timestamp_utc = data.get('timestamp_utc')
        severity = data.get('severity', 'warning')
        source = data.get('source', 'unknown')
        file_path = data.get('file', '')
        line_number = data.get('line_no')
        message = data.get('message', '')
        fingerprint = data.get('fingerprint', '')
        context = data.get('context', [])
        pattern_matched = data.get('pattern_matched', '')
        
        # Get or create system
        system, created = System.objects.get_or_create(
            hostname=host,
            defaults={
                'name': host,
                'ip_address': request.META.get('REMOTE_ADDR', '0.0.0.0'),
                'status': 'online',
                'last_seen': timezone.now()
            }
        )
        
        if not created:
            system.last_seen = timezone.now()
            system.save()
        
        # Get or create application
        application, created = Application.objects.get_or_create(
            name=source,
            system=system,
            defaults={
                'agent_type': 'appmon',
                'status': 'active',
                'version': data.get('version', '2.0.0'),
                'last_seen': timezone.now()
            }
        )
        
        if not created:
            application.last_seen = timezone.now()
            application.save()
        
        # Create application alert
        alert = ApplicationAlert.objects.create(
            application=application,
            title=f"{severity.upper()} Alert - {source}",
            message=message,
            severity=severity,
            status='active',
            source_name=source,
            file_path=file_path,
            line_number=line_number,
            pattern_matched=pattern_matched,
            context_lines=context,
            fingerprint=fingerprint,
            metadata=data.get('metadata', {})
        )
        
        # Create log entry
        LogEntry.objects.create(
            system=system,
            level='WARNING' if severity == 'warning' else 'ERROR',
            source='application',
            message=f"AppMon Alert: {message}",
            details={
                'source': source,
                'file': file_path,
                'line_number': line_number,
                'pattern_matched': pattern_matched,
                'fingerprint': fingerprint,
                'service': service
            },
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return JsonResponse({'status': 'success', 'alert_id': alert.id})
        
    except Exception as e:
        logger.error(f"Error processing AppMon alert: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def appmon_metrics_endpoint(request):
    """
    Endpoint to receive metrics from AppMon agents
    """
    try:
        data = json.loads(request.body)
        logger.info(f"Received AppMon metrics from {data.get('host', 'unknown')}")
        
        host = data.get('host')
        metrics_data = data.get('metrics', {})
        timestamp_utc = data.get('timestamp_utc')
        
        # Get or create system
        system, created = System.objects.get_or_create(
            hostname=host,
            defaults={
                'name': host,
                'ip_address': request.META.get('REMOTE_ADDR', '0.0.0.0'),
                'status': 'online',
                'last_seen': timezone.now()
            }
        )
        
        if not created:
            system.last_seen = timezone.now()
            system.save()
        
        # Get or create application (use hostname as default app name)
        application, created = Application.objects.get_or_create(
            name=f"AppMon-{host}",
            system=system,
            defaults={
                'agent_type': 'appmon',
                'status': 'active',
                'version': data.get('version', '2.0.0'),
                'last_seen': timezone.now()
            }
        )
        
        if not created:
            application.last_seen = timezone.now()
            application.save()
        
        # Create application metrics
        app_metrics = ApplicationMetrics.objects.create(
            application=application,
            files_monitored=metrics_data.get('files_monitored', 0),
            total_log_size_mb=metrics_data.get('total_log_size_mb', 0.0),
            largest_file_mb=metrics_data.get('largest_file_mb', 0.0),
            total_alerts_sent=metrics_data.get('total_alerts_sent', 0),
            unique_alerts_sent=metrics_data.get('unique_alerts_sent', 0),
            duplicate_alerts_suppressed=metrics_data.get('duplicate_alerts_suppressed', 0),
            scan_duration_ms=metrics_data.get('last_scan_duration_ms', 0.0),
            scan_frequency_per_minute=metrics_data.get('scan_frequency_per_minute', 0.0),
            active_sources=metrics_data.get('active_sources', 0),
            total_patterns=metrics_data.get('total_patterns', 0),
            errors_count=metrics_data.get('errors_last_hour', 0),
            alert_cache_size=metrics_data.get('alert_cache_size', 0),
            cache_hit_rate=metrics_data.get('cache_hit_rate', 0.0),
            details=metrics_data
        )
        
        return JsonResponse({'status': 'success', 'metrics_id': app_metrics.id})
        
    except Exception as e:
        logger.error(f"Error processing AppMon metrics: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def appmon_agents_list(request):
    """
    List all AppMon agents and their status
    """
    applications = Application.objects.filter(agent_type='appmon').order_by('-last_seen')
    serializer = ApplicationSerializer(applications, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def appmon_agent_detail(request, application_id):
    """
    Get detailed information about a specific AppMon agent
    """
    try:
        application = Application.objects.get(id=application_id, agent_type='appmon')
        serializer = ApplicationSerializer(application)
        return Response(serializer.data)
    except Application.DoesNotExist:
        return Response({'error': 'Application not found'}, status=404)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def appmon_agent_metrics(request, application_id):
    """
    Get metrics history for a specific AppMon agent
    """
    try:
        application = Application.objects.get(id=application_id, agent_type='appmon')
        metrics = ApplicationMetrics.objects.filter(application=application).order_by('-timestamp')[:100]
        serializer = ApplicationMetricsSerializer(metrics, many=True)
        return Response(serializer.data)
    except Application.DoesNotExist:
        return Response({'error': 'Application not found'}, status=404)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def appmon_alerts_list(request):
    """
    List all AppMon alerts
    """
    alerts = ApplicationAlert.objects.filter(application__agent_type='appmon').order_by('-created_at')
    serializer = ApplicationAlertSerializer(alerts, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def appmon_alert_acknowledge(request, alert_id):
    """
    Acknowledge an AppMon alert
    """
    try:
        alert = ApplicationAlert.objects.get(id=alert_id)
        alert.status = 'acknowledged'
        alert.acknowledged_at = timezone.now()
        alert.acknowledged_by = request.user
        alert.save()
        
        serializer = ApplicationAlertSerializer(alert)
        return Response(serializer.data)
    except ApplicationAlert.DoesNotExist:
        return Response({'error': 'Alert not found'}, status=404)
