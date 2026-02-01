from django_multitenant.utils import set_current_tenant
from .models import Tenant

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # For now, we take the first tenant the user owns.
            # In a more complex setup, you might want to store the 
            # active tenant_id in the session.
            tenant = Tenant.objects.filter(owner=request.user).first()
            if tenant:
                set_current_tenant(tenant)
            else:
                # If user has no tenant, maybe create one automatically or handle appropriately
                set_current_tenant(None)
        else:
            set_current_tenant(None)

        response = self.get_response(request)
        return response
