"""
Admin System Settings URL Configuration
"""

from django.urls import path
from ..views.system_settings_views import get_settings, test_connection, health_check, switch_ai_mode

urlpatterns = [
    path('settings/', get_settings, name='get_settings'),
    path('settings/test-connection/', test_connection, name='test_connection'),
    path('settings/switch-ai-mode/', switch_ai_mode, name='switch_ai_mode'),
    path('system/health/', health_check, name='admin_system_health'),
]


