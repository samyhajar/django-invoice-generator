from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Tenant, UserProfile

@receiver(post_save, sender=User)
def create_user_tenant_profile(sender, instance, created, **kwargs):
    if created:
        # Create a default tenant for the user
        tenant_name = f"{instance.username}'s Tenant"
        tenant = Tenant.objects.create(name=tenant_name, owner=instance)
        
        # Create UserProfile
        role = 'admin' if instance.is_superuser else 'user'
        UserProfile.objects.create(user=instance, tenant=tenant, role=role)

@receiver(post_save, sender=User)
def save_user_tenant_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
