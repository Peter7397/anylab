from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def task_list(request):
    """Placeholder view for maintenance task list"""
    return Response({'message': 'Maintenance task list endpoint - coming soon'})
