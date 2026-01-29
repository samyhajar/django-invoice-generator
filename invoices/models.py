from django.db import models
from decimal import Decimal
from django.core.exceptions import ValidationError


class CompanyProfile(models.Model):
    """Singleton model for company information (only one instance allowed)"""
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
        return self.company_name

    def save(self, *args, **kwargs):
        """Ensure only one instance exists (singleton pattern)"""
        if not self.pk and CompanyProfile.objects.exists():
            raise ValidationError('Only one Company Profile can exist.')
        return super().save(*args, **kwargs)

    @classmethod
    def get_instance(cls):
        """Get or create the singleton instance"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class Client(models.Model):
    """Client model for invoice recipients"""
    name = models.CharField(max_length=255)
    initials = models.CharField(max_length=2, default="??", help_text="e.g. PK for Philipp Krebs")
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.initials})"


class Project(models.Model):
    """Projects associated with a client"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=5, help_text="e.g. NI for Nike")
    slug = models.SlugField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = ['client', 'name']

    def __str__(self):
        return f"{self.client.name} - {self.name} ({self.abbreviation})"

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """Product/Service library for reusable invoice items"""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    default_unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (€{self.default_unit_price})"


class Invoice(models.Model):
    """Invoice model"""
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
        Generate automatic invoice number:
        #{global_seq}-{client_initials}-{client_seq}-{project_abbr}{project_seq}
        Example: #001-PK-01-NI01
        """
        if not self.project:
            return f"DRAFT-{self.pk or 'new'}"

        client = self.project.client
        
        # 1. Global sequence
        if not self.global_sequence:
            last_global = Invoice.objects.order_by('-global_sequence').first()
            self.global_sequence = (last_global.global_sequence + 1) if last_global and last_global.global_sequence else 1
            
        # 2. Client sequence
        if not self.client_sequence:
            last_client = Invoice.objects.filter(project__client=client).order_by('-client_sequence').first()
            self.client_sequence = (last_client.client_sequence + 1) if last_client and last_client.client_sequence else 1
            
        # 3. Project sequence
        if not self.project_sequence:
            last_project = Invoice.objects.filter(project=self.project).order_by('-project_sequence').first()
            self.project_sequence = (last_project.project_sequence + 1) if last_project and last_project.project_sequence else 1
        
        # Format strings
        g_seq = f"{self.global_sequence:03d}"
        c_seq = f"{self.client_sequence:02d}"
        p_seq = f"{self.project_sequence:02d}"
        
        return f"#{g_seq}-{client.initials.upper()}-{c_seq}-{self.project.abbreviation.upper()}{p_seq}"
    
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


class InvoiceItem(models.Model):
    """Invoice line item model"""
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
            company = CompanyProfile.get_instance()
            total_rate = company.mileage_base_rate + (Decimal(self.num_people - 1) * company.mileage_extra_person_rate)
            return self.quantity * total_rate
        
        return self.quantity * self.unit_price

    def get_unit_rate_display(self):
        """Helper to get the actual rate used for display"""
        if self.item_type == 'mileage':
            company = CompanyProfile.get_instance()
            return company.mileage_base_rate + (Decimal(self.num_people - 1) * company.mileage_extra_person_rate)
        return self.unit_price
