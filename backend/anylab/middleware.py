from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.conf import settings
import re

class LoginRequiredMiddleware:
    """
    Middleware to require authentication for all pages except login and admin.
    Note: Django admin has its own built-in protection that requires is_staff=True.
    This middleware allows admin requests to pass through, and Django admin will
    enforce the staff requirement.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Define URLs that don't require authentication
        # Note: All /api/* routes are handled separately (passed through to DRF)
        self.exempt_urls = [
            r'^admin/',  # Django admin handles its own authentication (requires is_staff)
            r'^static/',
            r'^media/',
            r'^login/',
            r'^logout/',
        ]
        self.exempt_patterns = [re.compile(pattern) for pattern in self.exempt_urls]

    def __call__(self, request):
        # Check if the request path is exempt from authentication
        path = request.path_info.lstrip('/')
        
        # Check if path matches any exempt patterns
        is_exempt = any(pattern.match(path) for pattern in self.exempt_patterns)
        
        # If it's an API request, let DRF handle all authentication
        # DRF views have their own @permission_classes and @authentication_classes
        # that will properly validate JWT tokens and handle access control
        if request.path.startswith('/api/'):
            # Allow all API requests to pass through to DRF views
            # DRF will handle JWT authentication and return 401 if needed
                return self.get_response(request)
        
        # If exempt (including admin), allow the request to proceed
        # Django admin will enforce is_staff requirement internally
        if is_exempt:
            return self.get_response(request)
        
        # Check if user is authenticated (for non-API web page requests only)
        if not request.user.is_authenticated:
            # For web requests, redirect to login
            return redirect('/login/')
        
        return self.get_response(request)
