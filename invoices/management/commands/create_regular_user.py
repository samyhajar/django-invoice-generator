from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from invoices.models import Tenant, UserProfile


class Command(BaseCommand):
    help = 'Creates a regular user with tenant if it does not exist'

    def handle(self, *args, **options):
        User = get_user_model()
        username = 'samyhajaruser'
        email = 'samyuser@example.com'
        password = 'samyto2508C/'

        if not User.objects.filter(username=username).exists():
            # Create the user (not superuser)
            user = User.objects.create_user(username, email, password)
            user.is_staff = True  # Allow admin access
            user.save()
            
            # The signal will automatically create a tenant and user profile
            self.stdout.write(self.style.SUCCESS(f'User "{username}" created successfully!'))
        else:
            self.stdout.write(self.style.WARNING(f'User "{username}" already exists.'))
