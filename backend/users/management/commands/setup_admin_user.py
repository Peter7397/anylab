"""
Django management command to setup admin user with full permissions.
This command will:
1. Create or update the admin user to be a superuser
2. Ensure the user has is_staff=True
3. Optionally assign the system_admin role
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import Role, UserRole

User = get_user_model()


class Command(BaseCommand):
    help = 'Setup admin user with full permissions (superuser + system_admin role)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Username of the admin user (default: admin)'
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password for the admin user (if creating new user)'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@anylab.local',
            help='Email for the admin user'
        )

    def handle(self, *args, **options):
        username = options['username']
        password = options.get('password')
        email = options['email']

        # Get or create the admin user
        try:
            user = User.objects.get(username=username)
            self.stdout.write(self.style.WARNING(f'User "{username}" already exists. Updating...'))
        except User.DoesNotExist:
            if not password:
                self.stdout.write(self.style.ERROR(
                    f'User "{username}" does not exist. Please provide --password to create it.'
                ))
                return
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(self.style.SUCCESS(f'Created user "{username}"'))

        # Make user a superuser and staff
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.save()

        self.stdout.write(self.style.SUCCESS(
            f'✓ Set is_superuser=True and is_staff=True for "{username}"'
        ))

        # Ensure system_admin role exists
        system_admin_role, created = Role.objects.get_or_create(
            name='system_admin',
            defaults={
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
                },
                'is_active': True,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created system_admin role'))
        else:
            self.stdout.write(self.style.WARNING('✓ system_admin role already exists'))

        # Assign system_admin role to user
        user_role, created = UserRole.objects.get_or_create(
            user=user,
            role=system_admin_role,
            defaults={'is_active': True}
        )

        if created:
            self.stdout.write(self.style.SUCCESS(
                f'✓ Assigned system_admin role to "{username}"'
            ))
        else:
            user_role.is_active = True
            user_role.save()
            self.stdout.write(self.style.SUCCESS(
                f'✓ system_admin role already assigned to "{username}" (activated)'
            ))

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Admin user "{username}" is now configured with full permissions!'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'   - is_superuser: {user.is_superuser}'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'   - is_staff: {user.is_staff}'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'   - system_admin role: Assigned'
        ))

