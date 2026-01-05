"""
Maintenance and cleanup Celery tasks.
"""

import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from ..models import ChatMessage

logger = logging.getLogger(__name__)


@shared_task(name='ai_assistant.tasks.purge_old_chat_messages')
def purge_old_chat_messages():
    """Delete chat messages older than 7 days for retention policy."""
    try:
        cutoff = timezone.now() - timedelta(days=7)
        deleted, _ = ChatMessage.objects.filter(created_at__lt=cutoff).delete()
        return {"status": "success", "deleted": deleted}
    except Exception as e:
        logger.error(f'Failed to purge old chat messages: {e}', exc_info=True)
        return {"status": "error", "error": str(e)}

