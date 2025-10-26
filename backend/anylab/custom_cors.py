from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

class CustomCorsMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        # Add CORS headers
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response['Access-Control-Allow-Credentials'] = 'true'
        return response
