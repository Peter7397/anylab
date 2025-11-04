from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.dateparse import parse_datetime
from django.db.models import Q

from ..models import ChatMessage
from ..serializers import ChatMessageSerializer


class ChatHistoryListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatMessageSerializer

    def get_queryset(self):
        user = self.request.user
        qs = ChatMessage.objects.filter(user=user).order_by('-created_at')
        channel = self.request.query_params.get('channel')
        if channel:
            qs = qs.filter(channel=channel)
        thread_id = self.request.query_params.get('thread_id')
        if thread_id:
            qs = qs.filter(thread_id=thread_id)
        return qs

    def list(self, request, *args, **kwargs):
        limit = request.query_params.get('limit')
        queryset = self.get_queryset()
        if limit:
            try:
                limit_int = max(1, min(int(limit), 500))
            except ValueError:
                limit_int = 200
            queryset = queryset[:limit_int]
        else:
            queryset = queryset[:200]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ChatMessageCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatMessageSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


