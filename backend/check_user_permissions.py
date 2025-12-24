#!/usr/bin/env python3
"""
Diagnostic script to check user permissions and roles
Usage: python check_user_permissions.py <username>
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anylab.settings')
django.setup()

from users.models import User, Role, UserRole
from users.permissions import get_merged_permissions_for_user


def check_user_permissions(username):
    """Check and display user permissions"""
    print(f"\n{'='*60}")
    print(f"PERMISSION DIAGNOSTIC FOR USER: {username}")
    print(f"{'='*60}\n")
    
    # 1. Check if user exists
    try:
        user = User.objects.get(username=username)
        print(f"✅ User found: {user.username}")
        print(f"   - Email: {user.email}")
        print(f"   - Is staff: {user.is_staff}")
        print(f"   - Is superuser: {user.is_superuser}")
        print(f"   - Is active: {user.is_active}")
    except User.DoesNotExist:
        print(f"❌ User '{username}' not found!")
        return
    
    # 2. Check assigned roles
    print(f"\n{'='*60}")
    print("ASSIGNED ROLES:")
    print(f"{'='*60}")
    user_roles = UserRole.objects.filter(user=user).select_related('role')
    
    if not user_roles.exists():
        print("⚠️  No roles assigned to this user")
    else:
        for ur in user_roles:
            status = "✅ ACTIVE" if ur.is_active else "❌ INACTIVE"
            print(f"\n{status} Role: {ur.role.name}")
            print(f"   Description: {ur.role.description}")
            print(f"   Assigned at: {ur.assigned_at}")
            print(f"   Assigned by: {ur.assigned_by.username if ur.assigned_by else 'System'}")
            print(f"   Permissions: {ur.role.permissions}")
    
    # 3. Check merged permissions
    print(f"\n{'='*60}")
    print("MERGED PERMISSIONS:")
    print(f"{'='*60}")
    merged_perms = get_merged_permissions_for_user(user)
    
    if not merged_perms.get('features'):
        print("⚠️  No feature permissions found")
    else:
        print("\nFeature Permissions:")
        for feature, enabled in merged_perms.get('features', {}).items():
            status = "✅" if enabled else "❌"
            print(f"   {status} {feature}: {enabled}")
    
    # 4. Check RAG permission specifically
    print(f"\n{'='*60}")
    print("RAG ACCESS CHECK:")
    print(f"{'='*60}")
    has_rag = merged_perms.get('features', {}).get('ai.rag', False)
    if has_rag or user.is_staff or user.is_superuser:
        print("✅ User HAS access to RAG features")
        if user.is_staff:
            print("   Reason: User is staff")
        elif user.is_superuser:
            print("   Reason: User is superuser")
        else:
            print("   Reason: User has ai.rag permission from role")
    else:
        print("❌ User DOES NOT have access to RAG features")
        print("\n   To fix this, assign the 'ai_rag_user' role:")
        print("   1. Log in as admin")
        print("   2. Go to User Management")
        print(f"   3. Assign 'ai_rag_user' role to user '{username}'")
    
    # 5. Check if ai_rag_user role exists
    print(f"\n{'='*60}")
    print("ROLE AVAILABILITY CHECK:")
    print(f"{'='*60}")
    try:
        rag_role = Role.objects.get(name='ai_rag_user')
        print(f"✅ 'ai_rag_user' role exists")
        print(f"   Description: {rag_role.description}")
        print(f"   Is active: {rag_role.is_active}")
        print(f"   Permissions: {rag_role.permissions}")
    except Role.DoesNotExist:
        print("❌ 'ai_rag_user' role NOT FOUND!")
        print("\n   To fix this, run:")
        print("   python manage.py seed_roles")
    
    print(f"\n{'='*60}\n")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python check_user_permissions.py <username>")
        sys.exit(1)
    
    username = sys.argv[1]
    check_user_permissions(username)

