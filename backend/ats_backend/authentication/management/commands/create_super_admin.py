from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from authentication.models import UserProfile


class Command(BaseCommand):
    help = 'Create a super admin user for the tenant system'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email for the super admin')
        parser.add_argument('password', type=str, help='Password for the super admin')
        parser.add_argument('--first-name', type=str, default='', help='First name')
        parser.add_argument('--last-name', type=str, default='', help='Last name')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.ERROR(f'User with email {email} already exists')
            )
            return

        # Create the user
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=True,
            is_superuser=True
        )

        # Create the user profile with SUPER_ADMIN role
        UserProfile.objects.create(
            user=user,
            role=UserProfile.Role.SUPER_ADMIN,
            # organization=None for super admin
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Super admin user created successfully:\n'
                f'Email: {email}\n'
                f'Username: {email}\n'
                f'Role: Super Admin'
            )
        )