"""
Product URL Configuration
"""

from django.urls import path
from ..views import product_views

urlpatterns = [
    path('available/', product_views.get_available_products, name='get_available_products'),
    path('<str:product_category>/documents/', product_views.get_product_documents, name='get_product_documents'),
]

