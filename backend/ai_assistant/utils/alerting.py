"""
Alerting System for Processing Failures

This module provides alerting functionality for processing failures,
including email and Slack notifications.
"""

import logging
from typing import Dict, List, Optional
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
import requests

logger = logging.getLogger(__name__)


class AlertManager:
    """
    Manages alerts for processing failures and system issues.
    
    Supports:
    - Email notifications
    - Slack webhook notifications
    - Configurable thresholds
    - Rate limiting to prevent alert spam
    """
    
    def __init__(self):
        # Email configuration
        self.email_enabled = getattr(settings, 'ALERT_EMAIL_ENABLED', False)
        self.email_from = getattr(settings, 'ALERT_EMAIL_FROM', 'noreply@anylab.local')
        self.email_recipients = getattr(settings, 'ALERT_EMAIL_RECIPIENTS', [])
        
        # Slack configuration
        self.slack_enabled = getattr(settings, 'ALERT_SLACK_ENABLED', False)
        self.slack_webhook_url = getattr(settings, 'ALERT_SLACK_WEBHOOK_URL', None)
        
        # Alert thresholds
        self.failure_rate_threshold = getattr(settings, 'ALERT_FAILURE_RATE_THRESHOLD', 0.1)  # 10%
        self.failure_count_threshold = getattr(settings, 'ALERT_FAILURE_COUNT_THRESHOLD', 5)  # 5 failures
        self.check_window_hours = getattr(settings, 'ALERT_CHECK_WINDOW_HOURS', 1)  # 1 hour window
        
        # Rate limiting (prevent alert spam)
        self.rate_limit_minutes = getattr(settings, 'ALERT_RATE_LIMIT_MINUTES', 15)  # Max 1 alert per 15 minutes
        self._last_alert_time: Dict[str, timezone.datetime] = {}
    
    def check_processing_failures(self) -> Dict[str, any]:
        """
        Check for processing failures and send alerts if thresholds are exceeded.
        
        Returns:
            Dict with check results and alert status
        """
        from ai_assistant.models import UploadedFile
        from django.db.models import Count, Q
        from django.utils import timezone
        
        cutoff_time = timezone.now() - timedelta(hours=self.check_window_hours)
        
        # Get processing statistics
        total_files = UploadedFile.objects.filter(uploaded_at__gte=cutoff_time).count()
        failed_files = UploadedFile.objects.filter(
            uploaded_at__gte=cutoff_time,
            processing_status__in=['failed', 'corrupted', 'no_text_available']
        ).count()
        
        if total_files == 0:
            return {
                'status': 'ok',
                'message': 'No files processed in check window',
                'total_files': 0,
                'failed_files': 0,
                'failure_rate': 0.0,
                'alert_sent': False,
            }
        
        failure_rate = failed_files / total_files
        
        # Check if thresholds are exceeded
        should_alert = (
            failure_rate >= self.failure_rate_threshold or
            failed_files >= self.failure_count_threshold
        )
        
        result = {
            'status': 'alert' if should_alert else 'ok',
            'total_files': total_files,
            'failed_files': failed_files,
            'failure_rate': failure_rate,
            'failure_rate_percent': failure_rate * 100,
            'threshold_rate': self.failure_rate_threshold * 100,
            'threshold_count': self.failure_count_threshold,
            'check_window_hours': self.check_window_hours,
            'alert_sent': False,
        }
        
        if should_alert:
            # Check rate limiting
            alert_key = 'processing_failures'
            if self._should_send_alert(alert_key):
                alert_sent = self._send_processing_failure_alert(
                    total_files=total_files,
                    failed_files=failed_files,
                    failure_rate=failure_rate
                )
                result['alert_sent'] = alert_sent
                if alert_sent:
                    self._last_alert_time[alert_key] = timezone.now()
        
        return result
    
    def _should_send_alert(self, alert_key: str) -> bool:
        """
        Check if alert should be sent (rate limiting).
        
        Args:
            alert_key: Unique key for this alert type
            
        Returns:
            True if alert should be sent, False if rate limited
        """
        if alert_key not in self._last_alert_time:
            return True
        
        last_alert = self._last_alert_time[alert_key]
        time_since_last = timezone.now() - last_alert
        
        return time_since_last >= timedelta(minutes=self.rate_limit_minutes)
    
    def _send_processing_failure_alert(
        self,
        total_files: int,
        failed_files: int,
        failure_rate: float
    ) -> bool:
        """
        Send alert for processing failures.
        
        Args:
            total_files: Total files processed in window
            failed_files: Number of failed files
            failure_rate: Failure rate (0.0 to 1.0)
            
        Returns:
            True if alert was sent successfully
        """
        subject = f'[AnyLab Alert] High Processing Failure Rate: {failure_rate*100:.1f}%'
        message = f"""
Processing Failure Alert

Summary:
- Total files processed: {total_files}
- Failed files: {failed_files}
- Failure rate: {failure_rate*100:.1f}%
- Threshold: {self.failure_rate_threshold*100:.1f}% or {self.failure_count_threshold} failures
- Check window: Last {self.check_window_hours} hour(s)

Action Required:
Please investigate the processing failures. Check logs and system health.

Time: {timezone.now().isoformat()}
        """.strip()
        
        success = False
        
        # Send email alert
        if self.email_enabled and self.email_recipients:
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=self.email_from,
                    recipient_list=self.email_recipients,
                    fail_silently=False,
                )
                logger.info(f"Sent email alert for processing failures: {failed_files}/{total_files} failed")
                success = True
            except Exception as e:
                logger.error(f"Failed to send email alert: {e}")
        
        # Send Slack alert
        if self.slack_enabled and self.slack_webhook_url:
            try:
                slack_message = {
                    'text': subject,
                    'blocks': [
                        {
                            'type': 'section',
                            'text': {
                                'type': 'mrkdwn',
                                'text': f'*{subject}*\n\n{message}'
                            }
                        }
                    ]
                }
                
                response = requests.post(
                    self.slack_webhook_url,
                    json=slack_message,
                    timeout=10
                )
                response.raise_for_status()
                logger.info(f"Sent Slack alert for processing failures: {failed_files}/{total_files} failed")
                success = True
            except Exception as e:
                logger.error(f"Failed to send Slack alert: {e}")
        
        return success
    
    def send_custom_alert(
        self,
        subject: str,
        message: str,
        severity: str = 'warning',
        alert_key: Optional[str] = None
    ) -> bool:
        """
        Send a custom alert.
        
        Args:
            subject: Alert subject/title
            message: Alert message
            severity: Alert severity (info, warning, error, critical)
            alert_key: Optional key for rate limiting (if None, uses subject)
            
        Returns:
            True if alert was sent successfully
        """
        if alert_key is None:
            alert_key = subject
        
        # Check rate limiting
        if not self._should_send_alert(alert_key):
            logger.debug(f"Alert rate limited: {alert_key}")
            return False
        
        success = False
        
        # Send email alert
        if self.email_enabled and self.email_recipients:
            try:
                send_mail(
                    subject=f'[AnyLab {severity.upper()}] {subject}',
                    message=message,
                    from_email=self.email_from,
                    recipient_list=self.email_recipients,
                    fail_silently=False,
                )
                logger.info(f"Sent custom email alert: {subject}")
                success = True
            except Exception as e:
                logger.error(f"Failed to send custom email alert: {e}")
        
        # Send Slack alert
        if self.slack_enabled and self.slack_webhook_url:
            try:
                color_map = {
                    'info': '#36a64f',
                    'warning': '#ff9900',
                    'error': '#ff0000',
                    'critical': '#8b0000',
                }
                color = color_map.get(severity.lower(), '#808080')
                
                slack_message = {
                    'text': subject,
                    'blocks': [
                        {
                            'type': 'section',
                            'text': {
                                'type': 'mrkdwn',
                                'text': f'*[{severity.upper()}] {subject}*\n\n{message}'
                            }
                        }
                    ],
                    'attachments': [
                        {
                            'color': color,
                            'footer': f'AnyLab Alert System',
                            'ts': int(timezone.now().timestamp()),
                        }
                    ]
                }
                
                response = requests.post(
                    self.slack_webhook_url,
                    json=slack_message,
                    timeout=10
                )
                response.raise_for_status()
                logger.info(f"Sent custom Slack alert: {subject}")
                success = True
            except Exception as e:
                logger.error(f"Failed to send custom Slack alert: {e}")
        
        if success:
            self._last_alert_time[alert_key] = timezone.now()
        
        return success


# Global alert manager instance
alert_manager = AlertManager()

