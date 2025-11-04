from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from ..models import UploadedFile


def processing_health(request):
    now = timezone.now()
    last_hour = now - timedelta(hours=1)

    counts = {
        'pending': UploadedFile.objects.filter(processing_status='pending').count(),
        'extracting': UploadedFile.objects.filter(processing_status='metadata_extracting').count(),
        'chunking': UploadedFile.objects.filter(processing_status='chunking').count(),
        'embedding': UploadedFile.objects.filter(processing_status='embedding').count(),
        'ready': UploadedFile.objects.filter(processing_status='ready').count(),
        'failed': UploadedFile.objects.filter(processing_status='failed').count(),
    }

    recent_failed = list(
        UploadedFile.objects.filter(processing_status='failed', uploaded_at__gte=last_hour)
        .order_by('-uploaded_at')
        .values('id', 'filename', 'processing_error')[:10]
    )

    stale_pending = UploadedFile.objects.filter(
        processing_status='pending', uploaded_at__lt=now - timedelta(minutes=10)
    ).count()

    return JsonResponse({
        'status': 'ok',
        'timestamp': now.isoformat(),
        'counts': counts,
        'stale_pending_over_10m': stale_pending,
        'recent_failed_last_hour': recent_failed,
    })








