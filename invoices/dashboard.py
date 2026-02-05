from django.utils import timezone
from decimal import Decimal
from .models import Invoice, Client, Tenant, UserProfile
from .utils import calculate_progressive_tax
from django.contrib.auth import get_user_model

User = get_user_model()

def get_dashboard_stats(request, context):
    """
    Dashboard callback for django-unfold.
    Returns different stats based on user role:
    - Superadmin: System metrics (users, tenants, activity)
    - Tenant users: Financial metrics (revenue, invoices, VAT)
    """
    
    # Check if user is superadmin (no tenant association)
    is_superadmin = request.user.is_superuser
    
    if is_superadmin:
        # SUPERADMIN DASHBOARD: System metrics
        return get_superadmin_dashboard(request, context)
    else:
        # TENANT USER DASHBOARD: Financial metrics
        return get_tenant_dashboard(request, context)


def get_superadmin_dashboard(request, context):
    """Dashboard for superadmin showing system-wide metrics"""
    from django.utils.formats import number_format
    
    # Total counts
    total_users = User.objects.count()
    total_tenants = Tenant.objects.count()
    total_clients = Client.objects.count()
    total_user_profiles = UserProfile.objects.count()
    
    # Recent activity (last 30 days)
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    new_users_30d = User.objects.filter(date_joined__gte=thirty_days_ago).count()
    new_tenants_30d = Tenant.objects.filter(created_at__gte=thirty_days_ago).count()
    
    # Recent users
    recent_users = User.objects.order_by('-date_joined')[:10]
    recent_users_list = []
    for user in recent_users:
        try:
            tenant_name = user.profile.tenant.name if hasattr(user, 'profile') and user.profile.tenant else "No Tenant"
        except:
            tenant_name = "No Tenant"
        
        recent_users_list.append({
            'username': user.username,
            'email': user.email,
            'date_joined': user.date_joined,
            'tenant': tenant_name,
            'is_active': user.is_active,
        })
    
    context.update({
        "cards": [
            {
                "title": "Total Users",
                "metric": str(total_users),
                "footer": f"+{new_users_30d} in last 30 days",
                "icon": "person",
            },
            {
                "title": "Total Tenants",
                "metric": str(total_tenants),
                "footer": f"+{new_tenants_30d} in last 30 days",
                "icon": "business",
            },
            {
                "title": "Total Clients",
                "metric": str(total_clients),
                "footer": "Across all tenants",
                "icon": "groups",
            },
            {
                "title": "User Profiles",
                "metric": str(total_user_profiles),
                "footer": "Active user-tenant associations",
                "icon": "badge",
            },
        ],
        "recent_activity": recent_users_list,
    })
    
    return context


def get_tenant_dashboard(request, context):
    """Dashboard for tenant users showing financial metrics"""
    now = timezone.now()
    current_year = now.year
    
    # Role-based filtering within the tenant
    user_invoices = Invoice.objects.all()
    user_clients = Client.objects.all()
    
    if not request.user.is_superuser:
        try:
            profile = request.user.profile
            if profile.role == 'user':
                user_invoices = user_invoices.filter(creator=request.user)
                user_clients = user_clients.filter(creator=request.user)
        except Exception:
            pass

    # Calculate totals from paid invoices (All time)
    all_paid = user_invoices.filter(status='paid')
    gross_total_paid = sum(inv.get_gross_total() for inv in all_paid)
    vat_total_paid = sum(inv.calculate_vat() for inv in all_paid)
    
    # Calculate pending invoices
    pending_invoices = user_invoices.filter(status='sent')
    pending_revenue = sum(inv.get_gross_total() for inv in pending_invoices)
    
    # Tax Calculation for Current Year
    current_year_paid = all_paid.filter(date__year=current_year)
    current_year_net_revenue = sum(inv.get_net_total() for inv in current_year_paid)
    
    tax_data = calculate_progressive_tax(current_year_net_revenue, current_year)
    estimated_tax = tax_data.get('total_tax', Decimal('0.00'))
    effective_rate = tax_data.get('effective_rate', Decimal('0.00'))
    
    # Draft invoices
    draft_invoices_count = user_invoices.filter(status='draft').count()
    
    # Total invoices and clients
    total_invoices = user_invoices.count()
    total_clients = user_clients.count()
    
    # Calculate average invoice value
    avg_invoice = gross_total_paid / all_paid.count() if all_paid.count() > 0 else 0
    
    # This month's revenue
    this_month_invoices = user_invoices.filter(
        status='paid',
        date__year=now.year,
        date__month=now.month
    )
    this_month_revenue = sum(inv.get_gross_total() for inv in this_month_invoices)
    
    # Get recent invoices
    recent_invoices_qs = user_invoices.select_related('project__client').order_by('-date')[:10]
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

    from django.utils.formats import number_format

    context.update({
        "cards": [
            {
                "title": "Total Revenue (Paid)",
                "metric": f"{number_format(gross_total_paid, decimal_pos=2)} €",
                "footer": f"From {all_paid.count()} paid invoices",
                "icon": "payments",
            },
            {
                "title": "Pending Payments",
                "metric": f"{number_format(pending_revenue, decimal_pos=2)} €",
                "footer": f"{pending_invoices.count()} invoices awaiting payment",
                "icon": "pending_actions",
            },
            {
                "title": "This Month",
                "metric": f"{number_format(this_month_revenue, decimal_pos=2)} €",
                "footer": f"{this_month_invoices.count()} invoices paid",
                "icon": "calendar_month",
            },
            {
                "title": "Average Invoice",
                "metric": f"{number_format(avg_invoice, decimal_pos=2)} €",
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
                "title": "VAT Summary",
                "metric": f"{number_format(vat_total_paid, decimal_pos=2)} €",
                "footer": f"Total VAT collected (Paid)",
                "icon": "assessment",
                "link": "/admin/invoices/vatreport/",
                "class": "bg-primary-50 dark:bg-primary-900/20 border-primary-100 dark:border-primary-800",
            },
        ],
        "recent_invoices": recent_invoices,
    })
    
    return context
