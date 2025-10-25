from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response

# Create your views here.

@api_view(['GET'])
def system_list(request):
    """Placeholder view for system list"""
    return Response({'message': 'System list endpoint - coming soon'})
