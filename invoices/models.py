import uuid
from django.db import models
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.conf import settings
from .tenant_utils import TenantManager, get_current_tenant



class Tenant(models.Model):
    """Tenant model to separate data for different users/companies"""
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='tenants')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)




    @property
    def tenant_field(self):
        return 'id'

    @property
    def tenant_value(self):
        return self.id

    def __str__(self):


        return self.name

    class Meta:
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"


class UserProfile(models.Model):
    """User profile to store roles and tenant association"""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('user', 'User'),
        ('customer', 'Customer'),
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    objects = TenantManager()
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')





    def __str__(self):


        return f"{self.user.username} ({self.role})"


class TenantMixin(models.Model):
    """
    Mixin for tenant-aware models.
    Automatically sets tenant on save if not already set.
    """
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        # Auto-set tenant if not already set
        # Check if this model has a tenant field
        tenant_field = None
        for field in self._meta.fields:
            if field.name == 'tenant':
                tenant_field = field
                break
        
        if tenant_field:
            # Check if tenant is not set
            try:
                current_value = getattr(self, 'tenant_id', None)
                if not current_value:
                    current_tenant = get_current_tenant()
                    if current_tenant:
                        self.tenant = current_tenant
            except:
                # If there's any issue, try to set it anyway
                current_tenant = get_current_tenant()
                if current_tenant:
                    self.tenant = current_tenant
        
        super().save(*args, **kwargs)



class CompanyProfile(TenantMixin, models.Model):

    """Singleton model for company information (one per tenant)"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='company_profiles')
    objects = TenantManager()
    company_name = models.CharField(max_length=255, default="Your Company Name")
    display_company_name = models.BooleanField(default=True, verbose_name="Show Company Name on PDF")
    
    address = models.TextField(help_text="Full company address")
    display_address = models.BooleanField(default=True, verbose_name="Show Address on PDF")
    
    email = models.EmailField()
    display_email = models.BooleanField(default=True, verbose_name="Show Email on PDF")
    
    phone = models.CharField(max_length=50)
    display_phone = models.BooleanField(default=True, verbose_name="Show Phone on PDF")
    
    # Austria-specific fields
    uid = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name="UID",
        help_text="Umsatzsteuer-Identifikationsnummer (Austrian VAT ID)"
    )
    iban = models.CharField(
        max_length=34,
        blank=True,
        help_text="IBAN for bank transfers"
    )
    
    # Logo and branding
    logo = models.ImageField(upload_to='company/', blank=True, null=True)
    display_logo = models.BooleanField(default=True, verbose_name="Show Logo on PDF")
    
    # Payment information
    payment_terms = models.TextField(
        blank=True,
        help_text="Default payment terms/notes to display on invoices"
    )

    # Mileage rates
    mileage_base_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0.42'),
        verbose_name="Mileage Base Rate (€/km)"
    )
    mileage_extra_person_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0.05'),
        verbose_name="Extra Person Rate (€/km)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Company Profile"
        verbose_name_plural = "Company Profile"





    def __str__(self):


        return f"Profile for {self.tenant.name}"

    def save(self, *args, **kwargs):
        """Ensure only one instance exists per tenant"""
        if not self.pk and CompanyProfile.objects.filter(tenant=self.tenant).exists():
            raise ValidationError('Only one Company Profile can exist per tenant.')
        return super().save(*args, **kwargs)

    @classmethod
    def get_instance(cls, tenant):
        """Get or create the instance for the specific tenant"""
        obj, created = cls.objects.get_or_create(tenant=tenant)
        return obj


class Client(TenantMixin):
    """Client model for invoice recipients"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='clients')
    objects = TenantManager()
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_clients')
    name = models.CharField(max_length=255)
    name_extension = models.CharField(max_length=255, blank=True, null=True, verbose_name="Name Extension", help_text="e.g. Department, c/o, or second line")
    initials = models.CharField(max_length=2, default="??", help_text="e.g. PK for Philipp Krebs")
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    uid = models.CharField(max_length=50, blank=True, null=True, verbose_name="UID")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']





    def __str__(self):


        return f"{self.name} ({self.initials})"


class Project(TenantMixin):
    """Projects associated with a client"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='projects')
    objects = TenantManager()
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=5, help_text="e.g. NI for Nike")
    slug = models.SlugField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = ['tenant', 'client', 'name'] # Unique project name per client per tenant





    def __str__(self):


        return f"{self.client.name} - {self.name} ({self.abbreviation})"

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(TenantMixin):
    """Product/Service library for reusable invoice items"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='products')
    objects = TenantManager()
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    default_unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']





    def __str__(self):


        return f"{self.name} (€{self.default_unit_price})"


class Invoice(TenantMixin):
    """Invoice model"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='invoices')
    objects = TenantManager()
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_invoices')
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]

    LANGUAGE_CHOICES = [
        ('de', 'German'),
        ('en', 'English'),
    ]

    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    invoice_number = models.CharField(max_length=100, unique=True, blank=True, editable=False)
    
    # Sequence tracking
    global_sequence = models.PositiveIntegerField(editable=False, null=True, blank=True)
    client_sequence = models.PositiveIntegerField(editable=False, null=True, blank=True)
    project_sequence = models.PositiveIntegerField(editable=False, null=True, blank=True)
    
    date = models.DateField()
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='de')
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('20.00'))  # VAT percentage (Austria: 20%)
    
    # Austria-specific: MwSt vs VAT terminology
    VAT_LABEL_CHOICES = [
        ('mwst', 'MwSt (Mehrwertsteuer)'),
        ('vat', 'VAT'),
    ]
    vat_label = models.CharField(
        max_length=10,
        choices=VAT_LABEL_CHOICES,
        default='mwst',
        verbose_name="Tax Label"
    )
    
    notes = models.TextField(blank=True)
    payment_notes = models.TextField(
        blank=True,
        help_text="Custom payment instructions for this invoice (overrides company default)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-global_sequence']





    def __str__(self):


        return f"Invoice {self.invoice_number}"

    @property
    def gross_total(self):
        return self.get_gross_total()

    def get_net_total(self):
        """Calculate net total (sum of all items)"""
        return sum(item.total() for item in self.items.all())

    def calculate_vat(self):
        """Calculate VAT amount (only for items where apply_vat=True)"""
        vatable_net_total = sum(item.total() for item in self.items.all() if item.apply_vat)
        return vatable_net_total * (self.vat_rate / Decimal('100'))

    def get_gross_total(self):
        """Calculate gross total (net + VAT)"""
        return self.get_net_total() + self.calculate_vat()
    
    def _generate_invoice_number(self):
        """
        Generate global incrementing invoice number: YYYYMMDD-NNN
        Example: 20260201-001
        """
        # 1. Global sequence (always increments, even if projects differ or invoices canceled)
        if not self.global_sequence:
            from django.db.models import Max
            max_val = Invoice.objects.aggregate(Max('global_sequence'))['global_sequence__max']
            self.global_sequence = (max_val + 1) if max_val else 1
            
        # 2. Date part (YYYYMMDD)
        date_str = self.date.strftime('%Y%m%d')
        
        # 3. Format as #YYYYMMDDNNN
        return f"#{date_str}{self.global_sequence:03d}"
    
    def save(self, *args, **kwargs):
        """Override save to auto-generate sequences and number"""
        if not self.invoice_number:
            self.invoice_number = self._generate_invoice_number()
        super().save(*args, **kwargs)


class VATReport(Invoice):
    """Proxy model for specialized VAT reporting in admin"""
    class Meta:
        proxy = True
        verbose_name = "VAT Summary"
        verbose_name_plural = "VAT Summary"


class DocumentArchive(Client):
    """Proxy model for Document Archive/Folder structure view"""
    class Meta:
        proxy = True
        verbose_name = "Document Archive"
        verbose_name_plural = "Document Archive"


class EstimatedTax(Invoice):
    """Proxy model for Estimated Tax view in admin"""
    class Meta:
        proxy = True
        verbose_name = "Estimated Tax"
        verbose_name_plural = "Estimated Tax"


class InvoiceItem(TenantMixin):
    """Invoice line item model"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='invoice_items')
    objects = TenantManager()
    ITEM_TYPE_CHOICES = [
        ('service', 'Service / Leistung'),
        ('expense', 'Expense / Spesen'),
        ('mileage', 'Mileage / Kilometerstand'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES, default='service')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoice_items')
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Special fields
    apply_vat = models.BooleanField(default=True, verbose_name="Apply VAT")
    num_people = models.PositiveIntegerField(default=1, verbose_name="Number of People (for Mileage)")
    
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']





    def __str__(self):


        return f"{self.description} - {self.invoice.invoice_number}"

    def total(self):
        """Calculate line item total based on type"""
        if self.item_type == 'mileage':
            company = CompanyProfile.get_instance(self.tenant)
            total_rate = company.mileage_base_rate + (Decimal(self.num_people - 1) * company.mileage_extra_person_rate)
            return self.quantity * total_rate
        
        return self.quantity * self.unit_price

    def get_unit_rate_display(self):
        """Helper to get the actual rate used for display"""
        if self.item_type == 'mileage':
            company = CompanyProfile.get_instance(self.tenant)
            return company.mileage_base_rate + (Decimal(self.num_people - 1) * company.mileage_extra_person_rate)
        return self.unit_price


class TaxYear(TenantMixin):
    """Configuration for Tax Years to support historical data per tenant"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='tax_years')
    objects = TenantManager()
    year = models.PositiveIntegerField(help_text="e.g. 2024")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-year']
        unique_together = ['tenant', 'year']





    def __str__(self):


        return str(self.year)


class TaxBracket(TenantMixin):
    """Progressive tax brackets for a specific year per tenant"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='tax_brackets')
    objects = TenantManager()
    tax_year = models.ForeignKey(TaxYear, on_delete=models.CASCADE, related_name='brackets')
    lower_limit = models.DecimalField(max_digits=12, decimal_places=2, help_text="Income from this amount")
    upper_limit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Income up to this amount (leave blank for infinite)")
    rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Tax rate in percentage (e.g. 20.00)")
    description = models.CharField(max_length=255, blank=True, help_text="Label for display, e.g. '20% (12k-20k)'")
    
    class Meta:
        ordering = ['lower_limit']
        verbose_name = "Tax Bracket"
        verbose_name_plural = "Tax Brackets"





    def __str__(self):


        upper_str = f"€{self.upper_limit:,.0f}" if self.upper_limit else "∞"
        return f"{self.tax_year}: {self.rate}% (€{self.lower_limit:,.0f} - {upper_str})"
