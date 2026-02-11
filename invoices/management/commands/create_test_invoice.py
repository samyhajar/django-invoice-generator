"""
Django management command to create a test invoice for samyhajaruser
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from invoices.models import Invoice, InvoiceItem, Project, Client, Tenant
from decimal import Decimal
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Create a test invoice for samyhajaruser'

    def handle(self, *args, **options):
        # Get the user
        try:
            user = User.objects.get(username='samyhajaruser')
            self.stdout.write(f"Found user: {user.username}")
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('User "samyhajaruser" does not exist'))
            return

        # Get the user's tenant
        if not hasattr(user, 'profile') or not user.profile.tenant:
            self.stdout.write(self.style.ERROR('User does not have a profile or tenant'))
            return

        tenant = user.profile.tenant
        self.stdout.write(f"Tenant: {tenant.name}")

        # Get or create a client
        client, created = Client.objects.get_or_create(
            tenant=tenant,
            name="Test Client GmbH",
            defaults={
                'initials': 'TC',
                'email': 'test@client.com',
                'address': 'Test Street 123\n1010 Vienna\nAustria',
            }
        )
        self.stdout.write(f"Client: {client.name} ({'created' if created else 'existing'})")

        # Get or create a project
        project, created = Project.objects.get_or_create(
            tenant=tenant,
            client=client,
            name="Test Project",
            defaults={
                'abbreviation': 'TP',
            }
        )
        self.stdout.write(f"Project: {project.name} ({'created' if created else 'existing'})")

        # Create invoice
        invoice = Invoice.objects.create(
            tenant=tenant,
            creator=user,
            project=project,
            date=date.today(),
            due_date=date.today() + timedelta(days=14),
            status='draft',
            language='de',
            vat_rate=Decimal('20.00'),
            vat_label='mwst',
            notes='Test invoice created via script'
        )
        self.stdout.write(self.style.SUCCESS(f"Created invoice: {invoice.invoice_number}"))

        # Create invoice items with localized decimal values
        items_data = [
            {
                'item_type': 'service',
                'title': 'Web Development',
                'description': 'Frontend development work',
                'quantity': Decimal('1.50'),  # Testing decimal with .50
                'unit_price': Decimal('100.00'),
                'apply_vat': True,
            },
            {
                'item_type': 'service',
                'title': 'Consulting',
                'description': 'Technical consulting',
                'quantity': Decimal('2.00'),
                'unit_price': Decimal('150.00'),
                'apply_vat': True,
            },
            {
                'item_type': 'expense',
                'title': 'Travel Expenses',
                'description': 'Train ticket Vienna-Salzburg',
                'quantity': Decimal('1.00'),
                'unit_price': Decimal('45.50'),
                'apply_vat': False,
            },
        ]

        for idx, item_data in enumerate(items_data):
            item = InvoiceItem.objects.create(
                tenant=tenant,
                invoice=invoice,
                order=idx,
                **item_data
            )
            self.stdout.write(f"  - Created item: {item.title} ({item.quantity} x €{item.unit_price})")

        # Calculate totals
        net_total = invoice.get_net_total()
        vat_amount = invoice.calculate_vat()
        gross_total = invoice.get_gross_total()

        self.stdout.write(self.style.SUCCESS('\nInvoice Summary:'))
        self.stdout.write(f"  Net Total: €{net_total}")
        self.stdout.write(f"  VAT ({invoice.vat_rate}%): €{vat_amount}")
        self.stdout.write(f"  Gross Total: €{gross_total}")
        self.stdout.write(f"\nInvoice URL: http://127.0.0.1:8000/dashboard/invoices/{invoice.id}/")
