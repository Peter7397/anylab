from django.urls import path
from ..views.chat_history_views import ChatHistoryListView, ChatMessageCreateView

urlpatterns = [
    # Support both with and without trailing slash
    path('history', ChatHistoryListView.as_view(), name='chat-history-no-slash'),
    path('history/', ChatHistoryListView.as_view(), name='chat-history'),
    path('message', ChatMessageCreateView.as_view(), name='chat-message-create-no-slash'),
    path('message/', ChatMessageCreateView.as_view(), name='chat-message-create'),
]


