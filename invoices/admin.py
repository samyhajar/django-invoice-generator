from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from unfold.admin import ModelAdmin, TabularInline
from .models import Tenant, Client, Project, Invoice, InvoiceItem, CompanyProfile, Product, VATReport, DocumentArchive, TaxYear, TaxBracket, EstimatedTax, UserProfile
from . import models as from_models

class RoleIsolatedAdmin(ModelAdmin):
    """Base class to isolate data by role within a tenant"""
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        
        try:
            profile = request.user.profile
            if profile.role == 'admin':
                return qs
            # For 'user' role, filter by creator
            if hasattr(self.model, 'creator'):
                return qs.filter(creator=request.user)
        except UserProfile.DoesNotExist:
            pass
        return qs

    def save_model(self, request, obj, form, change):
        if not change and hasattr(obj, 'creator'):
            obj.creator = request.user
        super().save_model(request, obj, form, change)

    def get_exclude(self, request, obj=None):
        """Hide tenant and creator fields for non-superusers"""
        exclude = super().get_exclude(request, obj)
        if exclude is None:
            exclude = []
        else:
            exclude = list(exclude)
            
        if not request.user.is_superuser:
            # Hide tenant and creator if they exist on the model
            model_fields = [f.name for f in self.model._meta.fields]
            if 'tenant' in model_fields:
                exclude.append('tenant')
            if 'creator' in model_fields:
                exclude.append('creator')
                
        return exclude

@admin.register(UserProfile)
class UserProfileAdmin(ModelAdmin):
    list_display = ['user', 'tenant', 'role']
    list_filter = ['role', 'tenant']
    search_fields = ['user__username', 'tenant__name']


@admin.register(Tenant)
class TenantAdmin(ModelAdmin):
    list_display = ['name', 'owner', 'created_at']
    search_fields = ['name', 'owner__username']


@admin.register(CompanyProfile)
class CompanyProfileAdmin(RoleIsolatedAdmin):
    """Admin for singleton CompanyProfile"""
    
    def has_add_permission(self, request):
        # Only allow adding if no instance exists for the tenant
        return not self.get_queryset(request).exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of company profile
        return False

    def changelist_view(self, request, extra_context=None):
        """Redirect directly to the singleton instance's edit page"""
        obj = self.get_queryset(request).first()
        if obj:
            return redirect(reverse(f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change", args=(obj.pk,)))
        # If no profile exists, redirect to the add page
        return redirect(reverse(f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_add"))
    
    fieldsets = (
        ('Company Essentials', {
            'fields': (
                ('company_name', 'display_company_name'),
                'address', 
                ('display_address',),
            ),
            'classes': ['unfold-grid', 'unfold-grid-cols-1 md:unfold-grid-cols-2', 'mb-8']
        }),
        ('Contact Details', {
            'fields': (
                ('email', 'display_email'),
                ('phone', 'display_phone'),
            ),
            'classes': ['unfold-grid', 'unfold-grid-cols-1 md:unfold-grid-cols-2', 'mb-8']
        }),
        ('Austrian Business Identity', {
            'fields': (
                ('uid', 'iban'),
            ),
            'description': 'Tax and banking information for Austrian compliance.',
            'classes': ['unfold-grid', 'unfold-grid-cols-1 md:unfold-grid-cols-2', 'mb-8']
        }),
        ('Branding', {
            'fields': (
                ('logo', 'display_logo'),
            ),
            'classes': ['unfold-grid', 'unfold-grid-cols-1', 'mb-8']
        }),
        ('Mileage Rates', {
            'fields': (
                ('mileage_base_rate', 'mileage_extra_person_rate'),
            ),
            'description': 'Universal rates used for mileage calculations across all projects.',
            'classes': ['unfold-grid', 'unfold-grid-cols-1 md:unfold-grid-cols-2', 'mb-8']
        }),
        ('Default Payment Terms', {
            'fields': (
                'payment_terms',
            ),
            'classes': ['unfold-grid', 'unfold-grid-cols-1', 'mb-4']
        }),
    )


@admin.register(VATReport)
class VATReportAdmin(RoleIsolatedAdmin):
    list_display = ['invoice_number', 'get_client', 'date', 'get_net_total_display', 'get_vat_display', 'get_gross_total_display', 'status_badge']
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
            
            # Helper to determine quarter
            def get_quarter(date_obj):
                return (date_obj.month - 1) // 3 + 1

            # Calculate quarterly breakdown
            quarterly_data = {}
            
            for inv in queryset:
                year = inv.date.year
                quarter = get_quarter(inv.date)
                key = (year, quarter)
                
                if key not in quarterly_data:
                    quarterly_data[key] = {
                        'net': 0,
                        'vat': 0,
                        'gross': 0,
                        'count': 0
                    }
                
                quarterly_data[key]['net'] += inv.get_net_total()
                quarterly_data[key]['vat'] += inv.calculate_vat()
                quarterly_data[key]['gross'] += inv.get_gross_total()
                quarterly_data[key]['count'] += 1
            
            # Sort by Year DESC, Quarter DESC
            sorted_quarters = sorted(quarterly_data.items(), key=lambda x: x[0], reverse=True)
            
            quarterly_summary = []
            for (year, quarter), data in sorted_quarters:
                quarterly_summary.append({
                    'label': f"Q{quarter} {year}",
                    'net': data['net'],
                    'vat': data['vat'],
                    'gross': data['gross'],
                    'count': data['count']
                })
                
            response.context_data['quarterly_summary'] = quarterly_summary
        except (AttributeError, KeyError):
            pass
            
        return response

    @admin.display(description='Net Total (€)')
    def get_net_total_display(self, obj):
        from django.utils.formats import number_format
        return f"{number_format(obj.get_net_total(), decimal_pos=2)} €"

    @admin.display(description='VAT (€)')
    def get_vat_display(self, obj):
        from django.utils.formats import number_format
        return f"{number_format(obj.calculate_vat(), decimal_pos=2)} €"

    @admin.display(description='Gross Total (€)')
    def get_gross_total_display(self, obj):
        from django.utils.formats import number_format
        return f"{number_format(obj.get_gross_total(), decimal_pos=2)} €"

    @admin.display(description='Status')
    def status_badge(self, obj):
        from django.utils.html import format_html
        colors = {
            'paid': 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
            'sent': 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
            'draft': 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400',
            'canceled': 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
        }
        color_class = colors.get(obj.status, colors['draft'])
        return format_html(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {}">{}</span>',
            color_class,
            obj.get_status_display()
        )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Product)
class ProductAdmin(RoleIsolatedAdmin):
    list_display = ['name', 'default_unit_price', 'created_at']
    search_fields = ['name']


@admin.register(Client)
class ClientAdmin(RoleIsolatedAdmin):
    list_display = ['name', 'name_extension', 'initials', 'email', 'phone', 'uid', 'created_at']
    search_fields = ['name', 'name_extension', 'email', 'initials', 'uid']
    list_filter = ['created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (('name', 'name_extension'), 'initials')
        }),
        ('Contact Details', {
            'fields': ('email', 'phone', 'uid', 'address')
        }),
    )


@admin.register(Project)
class ProjectAdmin(RoleIsolatedAdmin):
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

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.item_type = 'service'
        return formset

class ExpenseItemInline(TabularInline):
    model = InvoiceItem
    extra = 1
    verbose_name = "Expense / Spesen"
    verbose_name_plural = "Expenses / Spesen"
    fields = ['description', 'quantity', 'unit_price', 'apply_vat', 'order']
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(item_type='expense')

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.item_type = 'expense'
        return formset

class MileageItemInline(TabularInline):
    model = InvoiceItem
    extra = 1
    verbose_name = "Mileage / Kilometerstand"
    verbose_name_plural = "Mileage / Kilometerstand"
    fields = ['description', 'quantity', 'num_people', 'order']
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(item_type='mileage')

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.item_type = 'mileage'
        return formset


@admin.register(Invoice)
class InvoiceAdmin(RoleIsolatedAdmin):
    list_display = ['invoice_number_display', 'client_display', 'date', 'gross_total_display', 'status_badge', 'view_pdf_link', 'mark_paid_button']
    list_filter = ['status', 'language', 'date', 'project__client']
    actions = ['make_paid', 'make_sent']

    @admin.display(description='Invoice #', ordering='invoice_number')
    def invoice_number_display(self, obj):
        return obj.invoice_number

    @admin.display(description='Client')
    def client_display(self, obj):
        return obj.project.client.name if obj.project else "-"

    @admin.display(description='Amount (Brutto)')
    def gross_total_display(self, obj):
        from django.utils.formats import number_format
        return f"{number_format(obj.get_gross_total(), decimal_pos=2)} €"

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

    def save_formset(self, request, form, formset, change):
        """
        Handle item_type assignment based on which inline the formset belongs to.
        Each inline sets formset.item_type in get_formset.
        """
        if formset.model == InvoiceItem:
            instances = formset.save(commit=False)
            item_type = getattr(formset, 'item_type', None)
            
            for instance in instances:
                if item_type:
                    instance.item_type = item_type
                
                # Special logic for mileage: usually no VAT
                if item_type == 'mileage':
                    instance.apply_vat = False
                    
                instance.save()
            formset.save_m2m()
            
            # Handle deletions
            for obj in formset.deleted_objects:
                obj.delete()
        else:
            super().save_formset(request, form, formset, change)
    readonly_fields = ['invoice_number', 'view_pdf_link']
    exclude = ['vat_label', 'payment_notes']

    class Media:
        js = ('js/admin_autofill.js',)

    
    @admin.display(description='Status')
    def status_badge(self, obj):
        from django.utils.html import format_html
        colors = {
            'paid': 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
            'sent': 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
            'draft': 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400',
            'canceled': 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
        }
        color_class = colors.get(obj.status, colors['draft'])
        return format_html(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {}">{}</span>',
            color_class,
            obj.get_status_display()
        )

    def get_gross_total(self, obj):
        from django.utils.formats import number_format
        return f"{number_format(obj.get_gross_total(), decimal_pos=2)} €"
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
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
        return redirect(f'admin:{opts.app_label}_{opts.model_name}_changelist')

    def mark_paid_button(self, obj):
        from django.utils.html import format_html
        from django.urls import reverse
        
        if obj.status == 'sent':
            url = reverse('admin:invoice-mark-as-paid', args=[obj.pk])
            return format_html(
                '<a href="{}" title="Mark as Paid" class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-primary-100 text-primary-700 hover:bg-primary-200 dark:bg-primary-900/40 dark:text-primary-300 dark:hover:bg-primary-900/60 transition-colors">'
                '<span class="material-symbols-outlined text-sm">check_circle</span>'
                '<span>Pay</span>'
                '</a>',
                url
            )
        return "-"
    mark_paid_button.short_description = "Action"
    mark_paid_button.allow_tags = True


@admin.register(from_models.EstimatedTax)
class EstimatedTaxAdmin(RoleIsolatedAdmin):
    change_list_template = "invoices/tax_detail.html"

    def has_module_permission(self, request):
        return False

    def changelist_view(self, request, extra_context=None):
        from django.utils import timezone
        from .utils import calculate_progressive_tax
        from .models import Invoice
        
        now = timezone.now()
        current_year = now.year
        
        # Calculate totals from paid invoices (Current Year)
        all_paid = Invoice.objects.filter(status='paid', date__year=current_year)
        gross_revenue = sum(inv.get_gross_total() for inv in all_paid)
        net_revenue = sum(inv.get_net_total() for inv in all_paid)
        
        tax_data = calculate_progressive_tax(net_revenue, current_year)
        
        extra_context = extra_context or {}
        extra_context.update({
            'year': current_year,
            'gross_revenue': gross_revenue,
            'net_revenue': net_revenue,
            'tax_data': tax_data,
            'brackets': tax_data.get('brackets', []),
            'total_tax': tax_data.get('total_tax', 0),
            'net_after_tax': net_revenue - tax_data.get('total_tax', 0),
            'effective_rate': tax_data.get('effective_rate', 0),
            # Unfold breadcrumbs support
            'title': f'Estimated Tax {current_year}',
        })
        
        return super().changelist_view(request, extra_context=extra_context)

    def has_add_permission(self, request):
        return False
        
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False




@admin.register(from_models.DocumentArchive)
class DocumentArchiveAdmin(RoleIsolatedAdmin):
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

@admin.register(TaxYear)
class TaxYearAdmin(RoleIsolatedAdmin):
    list_display = ['year', 'active', 'created_at']
    list_filter = ['active']

    def has_module_permission(self, request):
        return False


@admin.register(TaxBracket)
class TaxBracketAdmin(RoleIsolatedAdmin):
    list_display = ['tax_year', 'rate', 'lower_limit', 'upper_limit']
    list_filter = ['tax_year']

    def has_module_permission(self, request):
        return False
