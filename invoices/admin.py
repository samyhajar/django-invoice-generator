from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import Client, Project, Invoice, InvoiceItem, CompanyProfile, Product, VATReport, DocumentArchive
from . import models as from_models


@admin.register(CompanyProfile)
class CompanyProfileAdmin(ModelAdmin):
    """Admin for singleton CompanyProfile"""
    
    def has_add_permission(self, request):
        # Only allow adding if no instance exists
        return not CompanyProfile.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of company profile
        return False
    
    fieldsets = (
        ('Company Information', {
            'fields': (
                ('company_name', 'display_company_name'),
                ('address', 'display_address'),
                ('email', 'display_email'),
                ('phone', 'display_phone'),
            )
        }),
        ('Austria-Specific', {
            'fields': ('uid', 'iban'),
            'description': 'Austrian tax and banking information'
        }),
        ('Branding', {
            'fields': (('logo', 'display_logo'),)
        }),
        ('Mileage Rates', {
            'fields': (('mileage_base_rate', 'mileage_extra_person_rate'),),
            'description': 'Configure universal rates for mileage calculations'
        }),
        ('Payment Terms', {
            'fields': ('payment_terms',)
        }),
    )


@admin.register(VATReport)
class VATReportAdmin(ModelAdmin):
    list_display = ['invoice_number', 'get_client', 'date', 'get_net_total_display', 'get_vat_display', 'get_gross_total_display', 'status']
    list_filter = ['date', 'status', 'project__client']
    readonly_fields = ['invoice_number', 'get_client', 'date', 'due_date', 'status', 'language', 'vat_rate']
    
    def get_client(self, obj):
        return obj.project.client.name
    get_client.short_description = 'Client'
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='paid')

    change_list_template = "admin/invoices/vatreport/change_list.html"

    def changelist_view(self, request, extra_context=None):
        # Calculate totals for the filtered queryset
        response = super().changelist_view(request, extra_context)
        
        try:
            cl = response.context_data['cl']
            queryset = cl.queryset
            
            # Calculate totals
            total_net = sum(inv.get_net_total() for inv in queryset)
            total_vat = sum(inv.calculate_vat() for inv in queryset)
            total_gross = sum(inv.get_gross_total() for inv in queryset)
            
            summary = {
                'net': total_net,
                'vat': total_vat,
                'gross': total_gross,
                'count': queryset.count()
            }
            
            response.context_data['summary'] = summary
        except (AttributeError, KeyError):
            pass
            
        return response

    @admin.display(description='Net Total (€)')
    def get_net_total_display(self, obj):
        return f"€{obj.get_net_total():.2f}"

    @admin.display(description='VAT (€)')
    def get_vat_display(self, obj):
        return f"€{obj.calculate_vat():.2f}"

    @admin.display(description='Gross Total (€)')
    def get_gross_total_display(self, obj):
        return f"€{obj.get_gross_total():.2f}"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ['name', 'default_unit_price', 'created_at']
    search_fields = ['name']


@admin.register(Client)
class ClientAdmin(ModelAdmin):
    list_display = ['name', 'initials', 'email', 'phone', 'created_at']
    search_fields = ['name', 'email', 'initials']
    list_filter = ['created_at']


@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    list_display = ['name', 'abbreviation', 'client', 'created_at']
    search_fields = ['name', 'abbreviation', 'client__name']
    list_filter = ['client', 'created_at']
    autocomplete_fields = ['client']


class ServiceItemInline(TabularInline):
    model = InvoiceItem
    extra = 1
    verbose_name = "Service / Leistung"
    verbose_name_plural = "Services / Leistungen"
    fields = ['product', 'description', 'quantity', 'unit_price', 'order']
    autocomplete_fields = ['product']
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(item_type='service')

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            instance.item_type = 'service'
            instance.save()
        formset.save_m2m()

class ExpenseItemInline(TabularInline):
    model = InvoiceItem
    extra = 1
    verbose_name = "Expense / Spesen"
    verbose_name_plural = "Expenses / Spesen"
    fields = ['description', 'quantity', 'unit_price', 'apply_vat', 'order']
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(item_type='expense')

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            instance.item_type = 'expense'
            instance.save()
        formset.save_m2m()

class MileageItemInline(TabularInline):
    model = InvoiceItem
    extra = 1
    verbose_name = "Mileage / Kilometerstand"
    verbose_name_plural = "Mileage / Kilometerstand"
    fields = ['description', 'quantity', 'num_people', 'order']
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(item_type='mileage')

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            instance.item_type = 'mileage'
            instance.apply_vat = False # Mileage usually no VAT in some contexts, but let user decide? User said "mwst is not applied" for spesen but mileage logic is separate.
            instance.save()
        formset.save_m2m()


@admin.register(Invoice)
class InvoiceAdmin(ModelAdmin):
    list_display = ['global_id_display', 'client_initials_display', 'client_seq_display', 'project_id_display', 'status', 'view_pdf_link', 'mark_paid_button']
    list_filter = ['status', 'language', 'date', 'project__client']
    actions = ['make_paid', 'make_sent']

    @admin.display(description='#', ordering='global_sequence')
    def global_id_display(self, obj):
        return f"{obj.global_sequence:03d}" if obj.global_sequence else "-"

    @admin.display(description='Client')
    def client_initials_display(self, obj):
        return obj.project.client.initials.upper() if obj.project else "-"

    @admin.display(description='Client #')
    def client_seq_display(self, obj):
        return f"{obj.client_sequence:02d}" if obj.client_sequence else "-"

    @admin.display(description='Project/Seq')
    def project_id_display(self, obj):
        if obj.project and obj.project_sequence:
            return f"{obj.project.abbreviation.upper()}{obj.project_sequence:02d}"
        return "-"

    @admin.action(description='Mark selected invoices as Paid')
    def make_paid(self, request, queryset):
        queryset.update(status='paid')

    @admin.action(description='Mark selected invoices as Sent')
    def make_sent(self, request, queryset):
        queryset.update(status='sent')
    
    search_fields = ['invoice_number', 'project__client__name']
    autocomplete_fields = ['project']
    date_hierarchy = 'date'
    inlines = [ServiceItemInline, ExpenseItemInline, MileageItemInline]
    readonly_fields = ['invoice_number', 'view_pdf_link']
    
    def get_gross_total(self, obj):
        return f"€{obj.get_gross_total():.2f}"
    get_gross_total.short_description = 'Gross Total'
    
    def view_pdf_link(self, obj):
        if obj.pk:
            from django.utils.html import format_html
            url = f'/invoice/{obj.pk}/pdf/'
            return format_html('<a href="{}" target="_blank">View PDF</a>', url)
        return "-"
    view_pdf_link.short_description = 'PDF'

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:invoice_id>/mark-as-paid/',
                self.admin_site.admin_view(self.mark_as_paid_view),
                name='invoice-mark-as-paid',
            ),
        ]
        return custom_urls + urls

    def mark_as_paid_view(self, request, invoice_id):
        from django.shortcuts import get_object_or_404, redirect
        from django.contrib import messages
        
        invoice = get_object_or_404(Invoice, pk=invoice_id)
        if invoice.status != 'paid':
            invoice.status = 'paid'
            invoice.save()
            self.message_user(request, f"Invoice {invoice.invoice_number} marked as paid.", messages.SUCCESS)
        else:
             self.message_user(request, f"Invoice {invoice.invoice_number} is already paid.", messages.WARNING)
             
        opts = self.model._meta
        return redirect(f'admin:{opts.app_label}_{opts.model_name}_changelist')

    def mark_paid_button(self, obj):
        from django.utils.html import format_html
        from django.urls import reverse
        
        if obj.status == 'sent':
            url = reverse('admin:invoice-mark-as-paid', args=[obj.pk])
            return format_html(
                '<a href="{}" title="Mark as Paid" class="text-green-600 hover:text-green-800 dark:text-green-400 dark:hover:text-green-300 transition-colors">'
                '<span class="material-symbols-outlined">payments</span>'
                '</a>',
                url
            )
        return "-"
    mark_paid_button.short_description = "Action"
    mark_paid_button.allow_tags = True


@admin.register(InvoiceItem)
class InvoiceItemAdmin(ModelAdmin):
    list_display = ['description', 'invoice', 'quantity', 'unit_price', 'get_total']
    list_filter = ['invoice__status']
    search_fields = ['description', 'invoice__invoice_number']
    
    def get_total(self, obj):
        return f"€{obj.total():.2f}"
    get_total.short_description = 'Total'


@admin.register(from_models.DocumentArchive)
class DocumentArchiveAdmin(ModelAdmin):
    change_list_template = "admin/invoices/documentarchive/change_list.html"

    def changelist_view(self, request, extra_context=None):
        # Handle ZIP download
        if request.GET.get('download-zip'):
            return self.download_zip_archive()

        # Prepare context for hierarchical view
        clients = Client.objects.prefetch_related('projects__invoices').all()
        client_data = []
        
        for client in clients:
            project_data = []
            total_client_invoices = 0
            for project in client.projects.all():
                invoices = project.invoices.all().order_by('-global_sequence')
                if not invoices.exists():
                    continue
                
                count = invoices.count()
                total_client_invoices += count
                invoice_list = []
                for inv in invoices:
                    invoice_list.append({
                        'id': inv.id,
                        'filename': f"{inv.invoice_number}.pdf",
                        'date': inv.date.strftime('%Y-%m-%d'),
                        'number': inv.invoice_number,
                        'amount': f"{inv.get_gross_total():.2f}"
                    })
                
                project_data.append({
                    'name': project.name,
                    'invoices_list': invoice_list,
                    'count': count
                })
            
            if project_data:
                client_data.append({
                    'name': client.name,
                    'projects': project_data,
                    'invoice_count': total_client_invoices
                })

        extra_context = extra_context or {}
        extra_context['clients'] = client_data
        
        return super().changelist_view(request, extra_context=extra_context)

    def download_zip_archive(self):
        """Generate and serve a ZIP file containing all invoices organized by Client/Project folders"""
        from django.http import HttpResponse
        import zipfile
        import io
        from invoices.views import generate_pdf_file

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            clients = Client.objects.prefetch_related('projects__invoices').all()
            
            for client in clients:
                client_folder = client.name.replace('/', '_')
                
                for project in client.projects.all():
                    project_folder = project.name.replace('/', '_')
                    
                    for invoice in project.invoices.all():
                        pdf_content = generate_pdf_file(invoice)
                        filename = f"{invoice.invoice_number}.pdf"
                        
                        # Add file to zip: Client Name/Project Name/ID.pdf
                        zip_path = f"{client_folder}/{project_folder}/{filename}"
                        zip_file.writestr(zip_path, pdf_content)

        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="invoices_archive.zip"'
        return response

    def has_add_permission(self, request):
        return False
        
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
