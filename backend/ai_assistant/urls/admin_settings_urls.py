"""
Admin System Settings URL Configuration
"""

from django.urls import path
from ..views.system_settings_views import get_settings, update_settings, get_available_models, test_connection, health_check, switch_ai_mode

urlpatterns = [
    path('settings/', get_settings, name='get_settings'),
    path('settings/update/', update_settings, name='update_settings'),
    path('settings/available-models/', get_available_models, name='get_available_models'),
    path('settings/test-connection/', test_connection, name='test_connection'),
    path('settings/switch-ai-mode/', switch_ai_mode, name='switch_ai_mode'),
    path('system/health/', health_check, name='admin_system_health'),
]


