from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import Role, UserRole
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    RoleSerializer, UserRoleSerializer
)
import json

User = get_user_model()

def login_view(request):
    """Web-based login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', '/')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'users/login.html')

def logout_view(request):
    """Web-based logout view"""
    logout(request)
    return redirect('/login/')

@login_required
def dashboard_view(request):
    """Dashboard view - requires authentication"""
    return render(request, 'users/dashboard.html', {
        'user': request.user
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    """API-based login view"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return Response({
                'error': 'Username and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            login(request, user)
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_staff': user.is_staff,
                },
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except json.JSONDecodeError:
        return Response({
            'error': 'Invalid JSON data'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_logout(request):
    """API-based logout view"""
    logout(request)
    return Response({
        'message': 'Logout successful'
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Get current user profile"""
    return Response({
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'is_staff': request.user.is_staff,
            'date_joined': request.user.date_joined,
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_list(request):
    """Get list of users"""
    if not request.user.is_staff:
        return Response({
            'error': 'Permission denied'
        }, status=status.HTTP_403_FORBIDDEN)
    
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response({
        'users': serializer.data
    })


# ============= Role Management Endpoints =============

@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def role_list_create(request):
    """List all roles or create a new role"""
    if request.method == 'GET':
        roles = Role.objects.all()
        serializer = RoleSerializer(roles, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = RoleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAdminUser])
def role_detail(request, role_id):
    """Get, update, or delete a role"""
    try:
        role = Role.objects.get(id=role_id)
    except Role.DoesNotExist:
        return Response({'error': 'Role not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = RoleSerializer(role)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = RoleSerializer(role, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        role.delete()
        return Response({'message': 'Role deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def assign_role(request):
    """Assign a role to a user"""
    user_id = request.data.get('user_id')
    role_id = request.data.get('role_id')
    
    if not user_id or not role_id:
        return Response({
            'error': 'user_id and role_id are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(id=user_id)
        role = Role.objects.get(id=role_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except Role.DoesNotExist:
        return Response({'error': 'Role not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if role is already assigned
    user_role, created = UserRole.objects.get_or_create(
        user=user,
        role=role,
        defaults={'assigned_by': request.user, 'is_active': True}
    )
    
    if not created:
        user_role.is_active = True
        user_role.save()
    
    serializer = UserRoleSerializer(user_role)
    return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def remove_role(request):
    """Remove a role from a user"""
    user_id = request.data.get('user_id')
    role_id = request.data.get('role_id')
    
    if not user_id or not role_id:
        return Response({
            'error': 'user_id and role_id are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user_role = UserRole.objects.get(user_id=user_id, role_id=role_id)
        user_role.is_active = False
        user_role.save()
        return Response({'message': 'Role removed successfully'}, status=status.HTTP_200_OK)
    except UserRole.DoesNotExist:
        return Response({'error': 'User role not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_roles(request, user_id):
    """Get all roles for a specific user"""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    user_roles = UserRole.objects.filter(user=user, is_active=True)
    serializer = UserRoleSerializer(user_roles, many=True)
    return Response(serializer.data)
