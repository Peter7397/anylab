from django.contrib import admin
from django.urls import path
from pdfimport import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='pdfimport/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
    path('', views.upload_pdf, name='upload'),
    path('query/', views.query_vector, name='query'),
    path('rag/', views.rag_query, name='rag_query'),
    path('lightweight-rag/', views.lightweight_rag_query, name='lightweight_rag_query'),
    path('documents/', views.document_list, name='document_list'),
    path('pdf/<int:uploaded_file_id>/', views.pdf_view, name='pdf_view'),
    
    # Serve media files directly through Django
    path('media/<path:path>', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]
