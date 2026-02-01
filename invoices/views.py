from decimal import Decimal
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from .models import Invoice, CompanyProfile, Product
from .storage import get_client_invoice_path, ensure_project_folder


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
    # VAT only applies to items where apply_vat=True (usually services)
    service_vat = sum(item.total() for item in service_items if item.apply_vat) * (invoice.vat_rate / Decimal('100'))
    service_gross = service_net + service_vat
    
    expense_total = sum(item.total() for item in expense_items)
    mileage_total = sum(item.total() for item in mileage_items)
    
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
        'expense_total': expense_total,
        'mileage_total': mileage_total,
        'gross_total': gross_total,
        'vat_label': vat_label,
        'payment_info': payment_info,
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
