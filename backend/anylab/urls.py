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
from users import views

@csrf_exempt
def health_check(request):
    """Health check endpoint for Docker"""
    return JsonResponse({"status": "healthy", "service": "anylab-backend"})

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Health check
    path('api/health/', health_check, name='health_check'),
    
    # JWT Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Web-based authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # API endpoints
    path('api/users/', include('users.urls')),
    path('api/monitoring/', include('monitoring.urls')),
    path('api/maintenance/', include('maintenance.urls')),
    path('api/ai/', include('ai_assistant.urls')),
]

# Always serve media files for now to fix the viewer issue
from django.views.static import serve

def media_serve(request, path):
    return serve(request, path, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    path('media/<path:path>', media_serve, name='media'),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
