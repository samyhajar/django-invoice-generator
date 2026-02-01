from .tenant_utils import set_current_tenant, clear_current_tenant
from .models import Tenant


class TenantMiddleware:
    """
    Middleware to set the current tenant based on the authenticated user.
    This enables automatic tenant filtering for all queries.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                # Get the user's tenant (from their profile or ownership)
                tenant = Tenant.objects.filter(owner=request.user).first()
                set_current_tenant(tenant)
            except Exception:
                clear_current_tenant()
        else:
            clear_current_tenant()

        response = self.get_response(request)
        
        # Clean up after request to avoid leaking tenant context
        clear_current_tenant()
        
        return response

