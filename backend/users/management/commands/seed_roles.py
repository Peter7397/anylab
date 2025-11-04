from django.core.management.base import BaseCommand

from users.models import Role


DEFAULT_ROLES = [
    {
        'name': 'system_admin',
        'description': 'Full administration access',
        'permissions': {
            'features': {
                'admin': True,
                'documents.upload': True,
                'documents.bulk_import': True,
                'help_portal.edit': True,
                'ai.rag': True,
                'knowledge.view': True,
                'forum.view': True,
                'forum.post': True,
                'forum.reply': True,
                'forum.edit': True,
                'forum.moderate': True,
                'forum.manage': True,
            }
        }
    },
    {
        'name': 'content_uploader',
        'description': 'Can upload single documents',
        'permissions': {
            'features': {
                'documents.upload': True,
                'knowledge.view': True,
                'forum.view': True,
                'forum.post': True,
                'forum.reply': True,
                'forum.edit': True,
            }
        }
    },
    {
        'name': 'bulk_importer',
        'description': 'Can bulk import documents and batches',
        'permissions': {
            'features': {
                'documents.bulk_import': True,
                'documents.upload': True,
                'knowledge.view': True,
                'forum.view': True,
                'forum.post': True,
                'forum.reply': True,
                'forum.edit': True,
            }
        }
    },
    {
        'name': 'help_portal_editor',
        'description': 'Can add and edit help portal content',
        'permissions': {
            'features': {
                'help_portal.edit': True,
                'forum.view': True,
                'forum.post': True,
                'forum.reply': True,
                'forum.edit': True,
            }
        }
    },
    {
        'name': 'ai_rag_user',
        'description': 'Can access AI RAG features',
        'permissions': {
            'features': {
                'ai.rag': True,
                'forum.view': True,
                'forum.post': True,
                'forum.reply': True,
                'forum.edit': True,
            }
        }
    },
    {
        'name': 'forum_moderator',
        'description': 'Can moderate forum posts and replies',
        'permissions': {
            'features': {
                'forum.view': True,
                'forum.post': True,
                'forum.reply': True,
                'forum.edit': True,
                'forum.moderate': True,
            }
        }
    },
    {
        'name': 'forum_user',
        'description': 'Can view, post, and reply in forum',
        'permissions': {
            'features': {
                'forum.view': True,
                'forum.post': True,
                'forum.reply': True,
                'forum.edit': True,
            }
        }
    },
    {
        'name': 'viewer',
        'description': 'Read-only viewer',
        'permissions': {
            'features': {
                'forum.view': True,
            }
        }
    },
]


class Command(BaseCommand):

    help = 'Seeds default roles with feature permissions'

    def handle(self, *args, **options):
        created = 0
        updated = 0

        for role_def in DEFAULT_ROLES:
            role, was_created = Role.objects.get_or_create(
                name=role_def['name'],
                defaults={
                    'description': role_def.get('description', ''),
                    'permissions': role_def.get('permissions', {}),
                    'is_active': True,
                }
            )
            if was_created:
                created += 1
            else:
                # Keep idempotent: update description/permissions if changed
                changed = False
                if role.description != role_def.get('description', ''):
                    role.description = role_def.get('description', '')
                    changed = True
                if role.permissions != role_def.get('permissions', {}):
                    role.permissions = role_def.get('permissions', {})
                    changed = True
                if changed:
                    role.save()
                    updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seeded roles. Created: {created}, Updated: {updated}"
        ))


