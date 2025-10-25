from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Placeholder for now - we'll add views later
    path('', views.user_list, name='user_list'),
] 