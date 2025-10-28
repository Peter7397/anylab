"""
Admin System Settings URL Configuration
"""

from django.urls import path
from ..views.system_settings_views import get_settings, test_connection

urlpatterns = [
    path('settings/', get_settings, name='get_settings'),
    path('settings/test-connection/', test_connection, name='test_connection'),
]


