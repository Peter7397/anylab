from rest_framework import permissions
from rest_framework.permissions import BasePermission
from .models import ForumPost, ForumReply


class ForumPublicOrAuthenticatedReadOnly(BasePermission):
    """
    Permission class for forum endpoints:
    - Public posts/replies: Readable by anyone
    - Non-public posts/replies: Readable by authenticated users
    - Creating/updating/deleting: Requires authentication
    """
    
    def has_permission(self, request, view):
        # Allow safe methods (GET, HEAD, OPTIONS) for public content
        if request.method in permissions.SAFE_METHODS:
            return True  # Check object-level permissions
        
        # Require authentication for write operations
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Allow safe methods
        if request.method in permissions.SAFE_METHODS:
            # Check if object is public visible
            if hasattr(obj, 'is_public_visible'):
                if obj.is_public_visible:
                    return True
                # Non-public: require authentication
                return request.user and request.user.is_authenticated
            # Default: require authentication for safe methods on non-public content
            return request.user and request.user.is_authenticated
        
        # Write operations: check ownership or admin
        if isinstance(obj, ForumPost):
            return obj.author == request.user or request.user.is_staff
        elif isinstance(obj, ForumReply):
            return obj.author == request.user or request.user.is_staff
        
        return False


class ForumCategoryPermission(BasePermission):
    """Permission for forum categories"""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            # Check if category allows public visibility
            if obj.is_public_visible:
                return True
            return request.user and request.user.is_authenticated
        
        # Write operations require admin
        return request.user and request.user.is_staff


class ForumPostWritePermission(BasePermission):
    """Permission for creating/updating forum posts"""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write operations require authentication
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Check if posting to public category without login is allowed
        if request.method == 'POST':
            category_id = request.data.get('category')
            if category_id:
                from .models import ForumCategory
                try:
                    category = ForumCategory.objects.get(id=category_id)
                    if category.allow_public_post:
                        return True
                except ForumCategory.DoesNotExist:
                    pass
        
        return True  # Authenticated users can post


class IsOwnerOrReadOnly(BasePermission):
    """Permission: only owner or admin can edit/delete"""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check ownership
        if hasattr(obj, 'author'):
            return obj.author == request.user or request.user.is_staff
        
        if hasattr(obj, 'uploaded_by'):
            return obj.uploaded_by == request.user or request.user.is_staff
        
        return False


class IsAdminOrReadOnly(BasePermission):
    """Permission: only admin can edit, anyone can read"""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

