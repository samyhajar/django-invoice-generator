from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date, timedelta
from ..models import Tenant, Client, Project, Invoice, InvoiceItem, CompanyProfile

class TitleDescriptionTest(TestCase):
    def setUp(self):
        # Create a tenant
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.tenant = Tenant.objects.create(name="Test Tenant", owner=self.user)
        
        # Create a client
        self.client_obj = Client.objects.create(
            tenant=self.tenant,
            name="Test Client",
            initials="TC"
        )
        
        # Create a project
        self.project_obj = Project.objects.create(
            tenant=self.tenant,
            client=self.client_obj,
            name="Test Project",
            abbreviation="TP"
        )
        
        # Create an invoice
        self.invoice = Invoice.objects.create(
            tenant=self.tenant,
            project=self.project_obj,
            date=date.today(),
            due_date=date.today() + timedelta(days=14),
            status='draft'
        )

    def test_expense_title_description(self):
        """Test that expense items can have both title and description"""
        expense = InvoiceItem.objects.create(
            tenant=self.tenant,
            invoice=self.invoice,
            item_type='expense',
            title="Taxi to Airport",
            description="Uber ride from home",
            quantity=Decimal('1.00'),
            unit_price=Decimal('45.00')
        )
        
        saved_expense = InvoiceItem.objects.get(pk=expense.pk)
        self.assertEqual(saved_expense.title, "Taxi to Airport")
        self.assertEqual(saved_expense.description, "Uber ride from home")

    def test_mileage_title_description(self):
        """Test that mileage items can have both title and description"""
        mileage = InvoiceItem.objects.create(
            tenant=self.tenant,
            invoice=self.invoice,
            item_type='mileage',
            title="Business Trip to Vienna",
            description="Customer meeting at HQ",
            quantity=Decimal('300.00'),
            num_people=1
        )
        
        saved_mileage = InvoiceItem.objects.get(pk=mileage.pk)
        self.assertEqual(saved_mileage.title, "Business Trip to Vienna")
        self.assertEqual(saved_mileage.description, "Customer meeting at HQ")
