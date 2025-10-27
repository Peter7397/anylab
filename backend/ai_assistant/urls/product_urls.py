"""
Product URL Configuration
"""

from django.urls import path
from ..views import product_views

urlpatterns = [
    path('<str:product_category>/documents/', product_views.get_product_documents, name='get_product_documents'),
]

