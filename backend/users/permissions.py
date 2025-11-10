from typing import Dict, Any

from rest_framework.permissions import BasePermission

from .models import UserRole


def get_merged_permissions_for_user(user) -> Dict[str, Any]:

    if user is None or not getattr(user, 'is_authenticated', False):
        return {}

    # Superusers and staff automatically get all permissions
    is_superuser = getattr(user, 'is_superuser', False)
    is_staff = getattr(user, 'is_staff', False)
    
    if is_superuser or is_staff:
        # Return all available features for superuser/staff
        # This grants access to all features without requiring explicit role assignments
        return {
            'features': {
                'ai.rag': True,
                'knowledge.view': True,
                'admin': True,
                'documents.upload': True,  # Added: Allow document uploads
                'documents.bulk_import': True,  # Added: Allow bulk imports
                'help_portal.edit': True,  # Added: Allow help portal editing
                'forum.view': True,
                'forum.post': True,
                'forum.reply': True,
                'forum.edit': True,
                'forum.moderate': True,
                'forum.manage': True,
            },
            'api': {},
            'routes': [],
        }

    active_user_roles = UserRole.objects.select_related('role').filter(user=user, is_active=True)

    merged: Dict[str, Any] = {
        'features': {},
    }

    for user_role in active_user_roles:
        role_permissions = user_role.role.permissions or {}

        # Merge features (boolean OR semantics)
        role_features = role_permissions.get('features', {}) or {}
        for feature_key, is_enabled in role_features.items():
            merged.setdefault('features', {})
            merged['features'][feature_key] = bool(merged['features'].get(feature_key) or is_enabled)

        # Shallow merge for optional sections like 'api' and 'routes'
        for section_key in ('api', 'routes'):
            section = role_permissions.get(section_key)
            if section is None:
                continue
            if section_key == 'api':
                merged.setdefault('api', {})
                for api_key, allowed in section.items():
                    merged['api'][api_key] = bool(merged['api'].get(api_key) or allowed)
            elif section_key == 'routes':
                merged.setdefault('routes', [])
                for route in section:
                    if route not in merged['routes']:
                        merged['routes'].append(route)

    return merged


class HasFeaturePermission(BasePermission):

    required_feature_key: str = ''

    def __init__(self, required_feature_key: str = '') -> None:
        super().__init__()
        self.required_feature_key = required_feature_key or self.required_feature_key

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        # Superusers bypass feature checks
        if getattr(request.user, 'is_superuser', False):
            return True
        if not self.required_feature_key:
            return True
        merged = get_merged_permissions_for_user(request.user)
        return bool(merged.get('features', {}).get(self.required_feature_key))

    @classmethod
    def require(cls, feature_key: str):
        class _FeaturePermission(cls):
            required_feature_key = feature_key
        return _FeaturePermission


