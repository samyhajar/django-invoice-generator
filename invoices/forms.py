from django import forms
from django.forms import inlineformset_factory
from .models import Invoice, InvoiceItem, Client, Project, CompanyProfile, Product

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['project', 'date', 'due_date', 'status', 'language', 'vat_rate', 'vat_label', 'notes', 'payment_notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    # We need to handle Client selection carefully. 
    # Logic: Select Client -> Filters Projects.
    # For now, standard select.
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Filter relations by tenant
        if self.tenant:
            # We don't have a direct 'client' field on Invoice, we have 'project'. 
            # But the UI usually wants to select Client then Project.
            # However, the model Invoice has 'project' FK.
            # Let's check models.py again. Invoice has 'project'.
            # It DOES NOT have 'client' directly.
            # But the user wants to "create invoice".
            
            # Wait, looking at models.py in step 21:
            # Invoice has: project = models.ForeignKey(Project, ...)
            # So we select Project.
            # But we should probably filter projects by tenant.
            self.fields['project'].queryset = Project.objects.filter(tenant=self.tenant)
            
            # Also need to add 'client' pseudo-field to help selection if UI requires it?
            # For simplicity, let's just let them select Project, which links to Client.
            # Or better: Group projects by client in the dropdown if possible or use javascript.
            
            # For this MVP step: just project select.
            pass

        # Add Tailwind classes to all fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm py-2 px-3'
            
            if field_name == 'notes' or field_name == 'payment_notes':
                 field.widget.attrs['rows'] = 3

class BaseInvoiceItemFormSet(forms.BaseInlineFormSet):
    pass

InvoiceItemFormSet = inlineformset_factory(
    Invoice, InvoiceItem,
    fields=['item_type', 'description', 'quantity', 'unit_price', 'apply_vat'],
    widgets={
        'item_type': forms.Select(attrs={'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-xs py-1 px-2'}),
        'description': forms.TextInput(attrs={'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-xs py-1 px-2'}),
        'quantity': forms.NumberInput(attrs={'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-xs py-1 px-2 text-right', 'step': '0.01'}),
        'unit_price': forms.NumberInput(attrs={'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-xs py-1 px-2 text-right', 'step': '0.01'}),
        'apply_vat': forms.CheckboxInput(attrs={'class': 'h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500'}),
    },
    extra=1,
    can_delete=True
)

class CompanyProfileForm(forms.ModelForm):
    class Meta:
        model = CompanyProfile
        fields = [
            'company_name', 'display_company_name',
            'address', 'display_address',
            'email', 'display_email',
            'phone', 'display_phone',
            'uid', 'iban',
            'logo', 'display_logo',
            'payment_terms',
            'mileage_base_rate', 'mileage_extra_person_rate'
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'payment_terms': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500'
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs['class'] = 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'
            else:
                field.widget.attrs['class'] = 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm py-2 px-3'

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'name_extension', 'initials', 'email', 'phone', 'address', 'uid']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm py-2 px-3'

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'default_unit_price', 'apply_vat']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm py-2 px-3'

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['client', 'name', 'abbreviation']

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm py-2 px-3'
        
        if self.tenant:
            self.fields['client'].queryset = Client.objects.filter(tenant=self.tenant)
