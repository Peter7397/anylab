"""
URL configuration for anylab project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from rest_framework.permissions import AllowAny
from users import views

# Override token views to allow unauthenticated access
class PublicTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]

class PublicTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]

class PublicTokenVerifyView(TokenVerifyView):
    permission_classes = [AllowAny]

@csrf_exempt
def health_check(request):
    """Health check endpoint for Docker"""
    return JsonResponse({"status": "healthy", "service": "anylab-backend"})

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Health check
    path('api/health/', health_check, name='health_check'),
    
    # JWT Authentication (public - no authentication required)
    path('api/token/', PublicTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', PublicTokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', PublicTokenVerifyView.as_view(), name='token_verify'),
    
    # Web-based authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # API endpoints
    path('api/users/', include('users.urls')),
    path('api/ai/', include('ai_assistant.urls')),
    path('api/forum/', include('forum.urls')),
]

# Always serve media files for now to fix the viewer issue
from django.views.static import serve

def media_serve(request, path):
    return serve(request, path, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    path('media/<path:path>', media_serve, name='media'),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
