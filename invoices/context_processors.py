from .models import CompanyProfile
from .tenant_utils import get_current_tenant

def company_context(request):
    """
    Adds the tenant-specific company profile to the context.
    This allows displaying the tenant's logo and name in the sidebar.
    """
    profile = None
    
    if request.user.is_authenticated:
        tenant = get_current_tenant()
        if tenant:
            try:
                profile = CompanyProfile.get_instance(tenant)
            except Exception:
                pass
    
    return {
        'tenant_company_profile': profile,
    }
