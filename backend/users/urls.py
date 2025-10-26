from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # User management
    path('', views.user_list, name='user_list'),
    path('profile/', views.user_profile, name='user_profile'),
    
    # Role management
    path('roles/', views.role_list_create, name='role_list_create'),
    path('roles/<int:role_id>/', views.role_detail, name='role_detail'),
    path('roles/assign/', views.assign_role, name='assign_role'),
    path('roles/remove/', views.remove_role, name='remove_role'),
    path('<int:user_id>/roles/', views.user_roles, name='user_roles'),
] 