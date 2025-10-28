"""
Help Portal URL Configuration
"""

from django.urls import path
from ..views import help_portal_views

urlpatterns = [
    path('', help_portal_views.list_help_portal_documents, name='help-portal-list'),
    path('statistics/', help_portal_views.help_portal_statistics, name='help-portal-statistics'),
    path('import/', help_portal_views.run_help_portal_import, name='help-portal-import'),
    path('check-duplicates/', help_portal_views.check_help_portal_duplicates, name='help-portal-check-duplicates'),
]

