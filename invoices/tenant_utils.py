"""
Custom multi-tenancy utilities for row-level tenant isolation.
This module provides thread-local tenant tracking and automatic query filtering.
"""
import threading
from django.db import models


# Thread-local storage for current tenant
_thread_locals = threading.local()


def set_current_tenant(tenant):
    """Set the current tenant for this thread/request"""
    _thread_locals.tenant = tenant


def get_current_tenant():
    """Get the current tenant for this thread/request"""
    return getattr(_thread_locals, 'tenant', None)


def clear_current_tenant():
    """Clear the current tenant (called at end of request)"""
    _thread_locals.tenant = None


class TenantQuerySet(models.QuerySet):
    """
    QuerySet that automatically filters by current tenant.
    All queries will be scoped to the current tenant unless explicitly bypassed.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_tenant_filter()
    
    def _add_tenant_filter(self):
        """Apply tenant filter if a tenant is set"""
        tenant = get_current_tenant()
        if tenant and hasattr(self.model, 'tenant'):
            # Use _filter_or_exclude to add the filter
            self.query.add_q(models.Q(tenant=tenant))
    
    def _clone(self):
        """Override clone to maintain tenant filtering"""
        clone = super()._clone()
        return clone


class TenantManager(models.Manager):
    """
    Manager that uses TenantQuerySet for automatic tenant filtering.
    Use this as the default manager for all tenant-aware models.
    """
    
    def get_queryset(self):
        qs = TenantQuerySet(self.model, using=self._db)
        tenant = get_current_tenant()
        if tenant:
            return qs.filter(tenant=tenant)
        return qs
    
    def all_tenants(self):
        """Bypass tenant filtering to get all records across all tenants"""
        return super().get_queryset()
