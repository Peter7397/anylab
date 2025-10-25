from django.urls import path
from . import views

app_name = 'maintenance'

urlpatterns = [
    # Placeholder for now - we'll add views later
    path('', views.task_list, name='task_list'),
] 