from django.urls import path
from . import views

app_name = 'monitoring'

urlpatterns = [
    # Placeholder for now - we'll add views later
    path('', views.system_list, name='system_list'),
] 