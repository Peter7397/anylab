from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def user_list(request):
    """Placeholder view for user list"""
    return Response({'message': 'User list endpoint - coming soon'})
