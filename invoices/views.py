from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from weasyprint import HTML
from .models import Invoice, CompanyProfile, Product, Project, Client
from .storage import get_client_invoice_path, ensure_project_folder
import zipfile
import io


def generate_pdf_file(invoice):
    """Generate raw PDF bytes for an invoice"""
    company = CompanyProfile.get_instance(invoice.tenant)
    
    # Determine VAT label based on invoice language
    vat_label = "MwSt" if invoice.language == 'de' else "VAT"
    
    # Use company default for payment info
    payment_info = company.payment_terms
    
    # Group items by type
    items = invoice.items.all()
    service_items = items.filter(item_type='service')
    expense_items = items.filter(item_type='expense')
    mileage_items = items.filter(item_type='mileage')
    
    # Calculate separate totals
    service_net = sum(item.total() for item in service_items)
    service_vat = sum(item.total() for item in service_items if item.apply_vat) * (invoice.vat_rate / Decimal('100'))
    service_gross = service_net + service_vat
    
    expense_net = sum(item.total() for item in expense_items)
    expense_vat = sum(item.total() for item in expense_items if item.apply_vat) * (invoice.vat_rate / Decimal('100'))
    expense_total = expense_net + expense_vat
    
    mileage_net = sum(item.total() for item in mileage_items)
    mileage_vat = sum(item.total() for item in mileage_items if item.apply_vat) * (invoice.vat_rate / Decimal('100'))
    mileage_total = mileage_net + mileage_vat
    
    gross_total = service_gross + expense_total + mileage_total
    
    # Render HTML template
    html_string = render_to_string('invoices/invoice_pdf.html', {
        'invoice': invoice,
        'client': invoice.project.client,
        'company': company,
        'service_items': service_items,
        'expense_items': expense_items,
        'mileage_items': mileage_items,
        'service_net': service_net,
        'service_vat': service_vat,
        'service_gross': service_gross,
        'expense_net': expense_net,
        'expense_vat': expense_vat,
        'expense_total': expense_total,
        'mileage_net': mileage_net,
        'mileage_vat': mileage_vat,
        'mileage_total': mileage_total,
        'gross_total': gross_total,
        'vat_label': vat_label,
        'payment_info': payment_info,
        'is_invalid': invoice.status == 'invalid',
    })
    
    # Generate PDF
    html = HTML(string=html_string)
    return html.write_pdf()


def generate_invoice_pdf(request, invoice_id):
    """Generate and return PDF for a specific invoice"""
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    pdf = generate_pdf_file(invoice)
    
    # Save PDF to hierarchical folder
    from .storage import ensure_project_folder, get_client_invoice_path
    ensure_project_folder(invoice.project.client.name, invoice.project.name)
    pdf_path = get_client_invoice_path(invoice.project.client.name, invoice.project.name, invoice.invoice_number)
    import os
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    with open(pdf_path, 'wb') as f:
        f.write(pdf)
    
    # Return PDF response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="invoice_{invoice.invoice_number}.pdf"'
    
    return response


def get_product_details(request, product_id):
    """API to get product details for admin auto-fill"""
    print(f"API Hit: get_product_details for product_id={product_id}")
    product = get_object_or_404(Product, pk=product_id)
    data = {
        'description': product.description,
        'unit_price': float(product.default_unit_price),
        'apply_vat': product.apply_vat,
    }
    print(f"Returning data: {data}")
    return JsonResponse(data)


def tax_overview(request):
    """Render detailed tax breakdown"""
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
    
    context = {
        'year': current_year,
        'gross_revenue': gross_revenue,
        'net_revenue': net_revenue,
        'tax_data': tax_data,
        'brackets': tax_data.get('brackets', []),
        'total_tax': tax_data.get('total_tax', 0),
        'net_after_tax': net_revenue - tax_data.get('total_tax', 0),
        'effective_rate': tax_data.get('effective_rate', 0),
    }
    
    return render(request, 'invoices/tax_detail.html', context)


def download_project_zip(request, project_id):
    """Generate and download a ZIP file containing all invoices for a project"""
    project = get_object_or_404(Project, pk=project_id)
    
    # Create in-memory ZIP
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        client_folder = project.client.name.replace('/', '_')
        
        for invoice in project.invoices.all():
            # Generate PDF content
            pdf_content = generate_pdf_file(invoice)
            
            # Filename: Client Name/InvoiceNumber.pdf
            filename = f"{client_folder}/{invoice.invoice_number}.pdf"
            zip_file.writestr(filename, pdf_content)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/zip')
    
    # filename: ClientName_ProjectName_Invoices.zip
    from django.utils.text import slugify
    zip_filename = f"{slugify(project.client.name)}_{slugify(project.name)}_invoices.zip"
    response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
    
    return response


# Frontend Dashboard Views

@login_required
def invoice_list(request):
    """Display list of invoices"""
    invoices = Invoice.objects.all().order_by('-date')
    return render(request, 'invoices/invoice_list.html', {'invoices': invoices})


@login_required
def client_list(request):
    """Display list of clients"""
    clients = Client.objects.all().order_by('name')
    return render(request, 'invoices/client_list.html', {'clients': clients})


@login_required
def product_list(request):
    """Display list of products"""
    products = Product.objects.all().order_by('name')
    return render(request, 'invoices/product_list.html', {'products': products})


@login_required
def project_list(request):
    """Display list of projects"""
    projects = Project.objects.all().order_by('-created_at')
    return render(request, 'invoices/project_list.html', {'projects': projects})


@login_required
def company_profile(request):
    """Display and edit company profile"""
    from .forms import CompanyProfileForm
    from .models import Tenant
    
    # Get tenant from user's profile or ownership
    tenant = None
    if hasattr(request.user, 'profile'):
        tenant = request.user.profile.tenant
    else:
        tenant = Tenant.objects.filter(owner=request.user).first()
    
    # Get or create company profile
    if tenant:
        profile = CompanyProfile.get_instance(tenant)
    else:
        # If no tenant, create a default one or get the first available
        profile, _ = CompanyProfile.objects.get_or_create(tenant=None)
    
    if request.method == 'POST':
        form = CompanyProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('company_profile')
    else:
        form = CompanyProfileForm(instance=profile)
    
    return render(request, 'invoices/company_profile.html', {
        'form': form,
        'instance': profile
    })


@login_required
def client_form(request, client_id=None):
    """Create or edit a client"""
    from .forms import ClientForm
    
    if client_id:
        client = get_object_or_404(Client, pk=client_id)
    else:
        client = None
    
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect('client_list')
    else:
        form = ClientForm(instance=client)
    
    return render(request, 'invoices/client_form.html', {'form': form})


@login_required
def product_form(request, product_id=None):
    """Create or edit a product"""
    from .forms import ProductForm
    
    if product_id:
        product = get_object_or_404(Product, pk=product_id)
    else:
        product = None
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'invoices/product_form.html', {'form': form})


@login_required
def project_form(request, project_id=None):
    """Create or edit a project"""
    from .forms import ProjectForm
    
    if project_id:
        project = get_object_or_404(Project, pk=project_id)
    else:
        project = None
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect('project_list')
    else:
        form = ProjectForm(instance=project)
    
    return render(request, 'invoices/project_form.html', {'form': form})


@login_required
def invoice_form(request, invoice_id=None):
    """Create or edit an invoice"""
    from .forms import InvoiceForm
    
    if invoice_id:
        invoice = get_object_or_404(Invoice, pk=invoice_id)
    else:
        invoice = None
    
    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            return redirect('invoice_list')
    else:
        form = InvoiceForm(instance=invoice)
    
    return render(request, 'invoices/invoice_form.html', {'form': form})


@login_required
def invoice_update(request, invoice_id):
    """Update an existing invoice"""
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    from .forms import InvoiceForm
    
    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            return redirect('invoice_list')
    else:
        form = InvoiceForm(instance=invoice)
    
    return render(request, 'invoices/invoice_update.html', {
        'form': form,
        'invoice': invoice
    })


# Public Pages

def home(request):
    """Home page"""
    return render(request, 'home.html')


def pricing(request):
    """Pricing page"""
    return render(request, 'pricing.html')


def signup(request):
    """User registration"""
    from django.contrib.auth.forms import UserCreationForm
    from django.contrib.auth import login
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('invoice_list')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/signup.html', {'form': form})
