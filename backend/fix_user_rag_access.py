#!/usr/bin/env python3
"""
Quick fix script to grant RAG access to a user
Usage: python fix_user_rag_access.py <username>
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


def fix_rag_access(username):
    """Grant RAG access to a user"""
    print(f"\n{'='*60}")
    print(f"GRANTING RAG ACCESS TO USER: {username}")
    print(f"{'='*60}\n")
    
    # 1. Check if user exists
    try:
        user = User.objects.get(username=username)
        print(f"✅ User found: {user.username}")
    except User.DoesNotExist:
        print(f"❌ User '{username}' not found!")
        print("\nAvailable users:")
        for u in User.objects.all()[:10]:
            print(f"   - {u.username}")
        return
    
    # 2. Check if ai_rag_user role exists
    try:
        rag_role = Role.objects.get(name='ai_rag_user')
        print(f"✅ 'ai_rag_user' role found")
    except Role.DoesNotExist:
        print("❌ 'ai_rag_user' role not found!")
        print("\nCreating roles...")
        from django.core.management import call_command
        call_command('seed_roles')
        rag_role = Role.objects.get(name='ai_rag_user')
        print("✅ Roles created")
    
    # 3. Assign or reactivate role
    user_role, created = UserRole.objects.get_or_create(
        user=user,
        role=rag_role,
        defaults={'is_active': True}
    )
    
    if created:
        print(f"✅ Role 'ai_rag_user' assigned to user '{username}'")
    else:
        if not user_role.is_active:
            user_role.is_active = True
            user_role.save()
            print(f"✅ Role 'ai_rag_user' reactivated for user '{username}'")
        else:
            print(f"ℹ️  Role 'ai_rag_user' already assigned and active")
    
    # 4. Verify permissions
    print(f"\n{'='*60}")
    print("VERIFICATION:")
    print(f"{'='*60}")
    perms = get_merged_permissions_for_user(user)
    has_rag = perms.get('features', {}).get('ai.rag', False)
    
    if has_rag:
        print("✅ SUCCESS! User now has RAG access")
        print("\nUser permissions:")
        for feature, enabled in perms.get('features', {}).items():
            print(f"   - {feature}: {enabled}")
        
        print(f"\n{'='*60}")
        print("NEXT STEPS:")
        print(f"{'='*60}")
        print(f"1. User '{username}' should LOG OUT completely")
        print("2. Clear browser cache (Ctrl+Shift+Delete)")
        print("3. Log back in")
        print("4. RAG features should now be visible in the sidebar")
    else:
        print("❌ FAILED! User still doesn't have RAG access")
        print("\nDebug info:")
        print(f"   User roles: {UserRole.objects.filter(user=user, is_active=True).count()}")
        print(f"   Merged permissions: {perms}")
    
    print(f"\n{'='*60}\n")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python fix_user_rag_access.py <username>")
        print("\nExample:")
        print("  python fix_user_rag_access.py test")
        sys.exit(1)
    
    username = sys.argv[1]
    fix_rag_access(username)

