from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response

# Create your views here.

@api_view(['GET'])
def chat_list(request):
    """Placeholder view for chat list"""
    return Response({'message': 'Chat list endpoint - coming soon'})
