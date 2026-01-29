from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from .models import Invoice, CompanyProfile
from .storage import get_client_invoice_path, ensure_project_folder


def generate_pdf_file(invoice):
    """Generate raw PDF bytes for an invoice"""
    company = CompanyProfile.get_instance()
    
    # Determine VAT label based on invoice setting
    vat_label = "MwSt" if invoice.vat_label == 'mwst' else "VAT"
    
    # Use invoice payment notes if provided, otherwise use company default
    payment_info = invoice.payment_notes if invoice.payment_notes else company.payment_terms
    
    # Group items by VAT applicability for two-table layout
    items = invoice.items.all()
    vatable_items = items.filter(apply_vat=True)
    non_vatable_items = items.filter(apply_vat=False)
    
    # Calculate subtotals
    vatable_net = sum(item.total() for item in vatable_items)
    vat_amount = invoice.calculate_vat()
    non_vatable_net = sum(item.total() for item in non_vatable_items)
    gross_total = vatable_net + vat_amount + non_vatable_net
    
    # Render HTML template
    html_string = render_to_string('invoices/invoice_pdf.html', {
        'invoice': invoice,
        'client': invoice.project.client,
        'company': company,
        'vatable_items': vatable_items,
        'non_vatable_items': non_vatable_items,
        'vatable_net': vatable_net,
        'non_vatable_net': non_vatable_net,
        'vat_amount': vat_amount,
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

