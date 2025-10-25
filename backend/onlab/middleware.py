from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.conf import settings
import re

class LoginRequiredMiddleware:
    """
    Middleware to require authentication for all pages except login and admin.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Define URLs that don't require authentication
        self.exempt_urls = [
            r'^admin/',
            r'^api/token/',
            r'^api/health/',
            r'^static/',
            r'^media/',
            r'^api/auth/login/',
            r'^api/auth/logout/',
            r'^login/',
            r'^logout/',
        ]
        self.exempt_patterns = [re.compile(pattern) for pattern in self.exempt_urls]

    def __call__(self, request):
        # Check if the request path is exempt from authentication
        path = request.path_info.lstrip('/')
        
        # Check if path matches any exempt patterns
        is_exempt = any(pattern.match(path) for pattern in self.exempt_patterns)
        
        # If it's an API request, check if it's an authentication endpoint
        if request.path.startswith('/api/'):
            is_exempt = is_exempt or request.path.startswith('/api/token/') or request.path.startswith('/api/health/')
            
            # For API requests with JWT tokens, let DRF handle authentication
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('Bearer '):
                # JWT token present, let DRF handle authentication
                return self.get_response(request)
        
        # If exempt, allow the request to proceed
        if is_exempt:
            return self.get_response(request)
        
        # Check if user is authenticated
        if not request.user.is_authenticated:
            # For API requests, return JSON response
            if request.path.startswith('/api/'):
                return JsonResponse({
                    'error': 'Authentication required',
                    'detail': 'Please log in to access this resource'
                }, status=401)
            
            # For web requests, redirect to login
            return redirect('/login/')
        
        return self.get_response(request)
