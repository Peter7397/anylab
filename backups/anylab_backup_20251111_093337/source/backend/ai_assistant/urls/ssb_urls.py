"""
SSB URL Configuration

NOTE: The old import endpoint is deprecated. All document uploads now
go through the standard document upload flow which creates embeddings.

If you need to keep this for some reason, uncomment the path below.
"""

from django.urls import path
# from ..views.ssb_views import import_ssb_file

urlpatterns = [
    # DEPRECATED: Now using standard document upload
    # path('import/', import_ssb_file, name='ssb_import'),
]
