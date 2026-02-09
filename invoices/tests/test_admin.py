from django.test import TestCase, Client as TestClient
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import date, timedelta
from invoices.models import Invoice, Client, Project, CompanyProfile, Tenant

class InvoiceAdminTest(TestCase):
    def setUp(self):
        # Create a superuser for admin access
        self.admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'password')
        self.client.login(username='admin', password='password')
        
        # Create tenant
        self.tenant = Tenant.objects.create(name="Test Tenant", owner=self.admin_user)
        
        # Create necessary data
        self.client_obj = Client.objects.create(
            tenant=self.tenant,
            name="Test Client",
            initials="TC",
            email="test@example.com",
            address="123 Test St"
        )
        
        self.project_obj = Project.objects.create(
            tenant=self.tenant,
            client=self.client_obj,
            name="Test Project",
            abbreviation="TP"
        )
        
        # Ensure company profile exists
        if not CompanyProfile.objects.exists():
            CompanyProfile.objects.create(
                tenant=self.tenant,
                company_name="My Company",
                email="me@mycompany.com",
                address="My Address",
                phone="1234567890"
            )

    def test_mark_as_paid_view(self):
        # Create a SENT invoice
        invoice = Invoice.objects.create(
            tenant=self.tenant,
            project=self.project_obj,
            date=date.today(),
            due_date=date.today() + timedelta(days=14),
            status='sent',
            language='en'
        )
        
        # Construct the URL for the custom action
        url = reverse('admin:invoice-mark-as-paid', args=[invoice.pk])
        
        # Perform GET request to the custom view
        response = self.client.get(url, follow=True)
        
        # Reload invoice from DB
        invoice.refresh_from_db()
        
        # Assertions
        self.assertEqual(invoice.status, 'paid')
        self.assertRedirects(response, reverse('admin:invoices_invoice_changelist'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertIn("marked as paid", str(messages[0]))

    def test_mark_as_paid_button_visibility(self):
        # Create a SENT invoice
        sent_invoice = Invoice.objects.create(
            tenant=self.tenant,
            project=self.project_obj,
            date=date.today(),
            due_date=date.today() + timedelta(days=14),
            status='sent'
        )
        
        # Create a PAID invoice
        paid_invoice = Invoice.objects.create(
            tenant=self.tenant,
            project=self.project_obj,
            date=date.today(),
            due_date=date.today() + timedelta(days=14),
            status='paid'
        )
        
        # Get the changelist page
        url = reverse('admin:invoices_invoice_changelist')
        response = self.client.get(url)
        
        # Check that the button link exists for SENT invoice
        mark_sent_url = reverse('admin:invoice-mark-as-paid', args=[sent_invoice.pk])
        self.assertContains(response, mark_sent_url)
        
        # Check that the button link does NOT exist for PAID invoice
        mark_paid_url = reverse('admin:invoice-mark-as-paid', args=[paid_invoice.pk])
        self.assertNotContains(response, mark_paid_url)
