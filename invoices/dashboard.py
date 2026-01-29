from django.utils import timezone
from decimal import Decimal
from .models import Invoice, Client

def get_dashboard_stats(request, context):
    """
    Dashboard callback for django-unfold.
    Returns comprehensive stats cards for the admin dashboard.
    """
    now = timezone.now()
    
    # Calculate totals from paid invoices
    all_paid = Invoice.objects.filter(status='paid')
    gross_total_paid = sum(inv.get_gross_total() for inv in all_paid)
    vat_total_paid = sum(inv.calculate_vat() for inv in all_paid)
    
    # Calculate pending invoices
    pending_invoices = Invoice.objects.filter(status='sent')
    pending_revenue = sum(inv.get_gross_total() for inv in pending_invoices)
    
    # Draft invoices
    draft_invoices = Invoice.objects.filter(status='draft')
    
    # Total invoices and clients
    total_invoices = Invoice.objects.count()
    total_clients = Client.objects.count()
    
    # Calculate average invoice value
    avg_invoice = gross_total_paid / all_paid.count() if all_paid.count() > 0 else 0
    
    # This month's revenue
    this_month_invoices = Invoice.objects.filter(
        status='paid',
        date__year=now.year,
        date__month=now.month
    )
    this_month_revenue = sum(inv.get_gross_total() for inv in this_month_invoices)
    
    # Get recent invoices
    recent_invoices_qs = Invoice.objects.select_related('project__client').order_by('-date')[:10]
    recent_invoices = []
    for inv in recent_invoices_qs:
        recent_invoices.append({
            'id': inv.id,
            'invoice_number': inv.invoice_number,
            'client': inv.project.client if inv.project else "No Project",
            'date': inv.date,
            'status': inv.status,
            'gross_total': inv.get_gross_total(),
        })

    context.update({
        "cards": [
            {
                "title": "Total Revenue (Paid)",
                "metric": f"€{gross_total_paid:,.2f}",
                "footer": f"From {all_paid.count()} paid invoices",
                "icon": "payments",
            },
            {
                "title": "Pending Payments",
                "metric": f"€{pending_revenue:,.2f}",
                "footer": f"{pending_invoices.count()} invoices awaiting payment",
                "icon": "pending_actions",
            },
            {
                "title": "This Month",
                "metric": f"€{this_month_revenue:,.2f}",
                "footer": f"{this_month_invoices.count()} invoices paid",
                "icon": "calendar_month",
            },
            {
                "title": "Average Invoice",
                "metric": f"€{avg_invoice:,.2f}",
                "footer": "Per paid invoice",
                "icon": "trending_up",
            },
            {
                "title": "Total Clients",
                "metric": str(total_clients),
                "footer": f"{total_invoices} total invoices",
                "icon": "groups",
            },
            {
                "title": "Draft Invoices",
                "metric": str(draft_invoices.count()),
                "footer": "Ready to send",
                "icon": "draft",
            },
        ],
        "recent_invoices": recent_invoices,
    })
    
    return context
