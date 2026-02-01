"""
Management command to set up standard user permissions.
This grants regular users access to invoice-related models but not admin models.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from invoices.models import (
    Client, Invoice, InvoiceItem, Project, Product, 
    CompanyProfile, TaxYear, TaxBracket, DocumentArchive,
    VATReport, EstimatedTax
)


class Command(BaseCommand):
    help = 'Grant standard permissions to a user for invoice management'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to grant permissions to')

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User "{username}" does not exist'))
            return

        # Models that regular users should have access to
        user_accessible_models = [
            Client,
            Invoice,
            InvoiceItem,
            Project,
            Product,
            CompanyProfile,
            TaxYear,
            TaxBracket,
            DocumentArchive,
            VATReport,
            EstimatedTax,
        ]

        # Grant all permissions for these models
        permissions_count = 0
        for model in user_accessible_models:
            content_type = ContentType.objects.get_for_model(model, for_concrete_model=False)
            perms = Permission.objects.filter(content_type=content_type)
            for perm in perms:
                user.user_permissions.add(perm)
                permissions_count += 1

        # Ensure user is staff (can access admin)
        if not user.is_staff:
            user.is_staff = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f'✅ Enabled staff access for {username}'))

        self.stdout.write(self.style.SUCCESS(f'✅ Granted {permissions_count} permissions to {username}'))
        self.stdout.write(self.style.SUCCESS(f'\n{username} now has access to:'))
        for model in user_accessible_models:
            self.stdout.write(f'  - {model.__name__}')
        
        self.stdout.write(self.style.WARNING(f'\n{username} does NOT have access to:'))
        self.stdout.write('  - Users')
        self.stdout.write('  - Groups')
        self.stdout.write('  - Tenants')
        self.stdout.write('  - User Profiles')
