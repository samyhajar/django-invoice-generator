from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from .models import (
    Tenant, UserProfile, Client, Invoice, InvoiceItem, 
    Project, Product, CompanyProfile, TaxYear, TaxBracket,
    DocumentArchive, VATReport, EstimatedTax
)


@receiver(post_save, sender=User)
def create_user_tenant_profile(sender, instance, created, **kwargs):
    if created:
        # Create a default tenant for the user
        tenant_name = f"{instance.username}'s Tenant"
        tenant = Tenant.objects.create(name=tenant_name, owner=instance)
        
        # Create UserProfile
        role = 'admin' if instance.is_superuser else 'user'
        UserProfile.objects.create(user=instance, tenant=tenant, role=role)
        
        # Grant standard permissions to non-superusers
        if not instance.is_superuser:
            # Models that regular users should have access to
            user_accessible_models = [
                Client, Invoice, InvoiceItem, Project, Product,
                CompanyProfile, TaxYear, TaxBracket,
                DocumentArchive, VATReport, EstimatedTax
            ]
            
            # Grant all permissions for these models
            for model in user_accessible_models:
                content_type = ContentType.objects.get_for_model(model, for_concrete_model=False)
                perms = Permission.objects.filter(content_type=content_type)
                for perm in perms:
                    instance.user_permissions.add(perm)
            
            # Ensure user is staff (can access admin)
            if not instance.is_staff:
                instance.is_staff = True
                instance.save()


@receiver(post_save, sender=User)
def save_user_tenant_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
