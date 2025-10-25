from django.urls import path
from . import views

app_name = 'ai_assistant'

urlpatterns = [
    # Placeholder for now - we'll add views later
    path('', views.chat_list, name='chat_list'),
] 