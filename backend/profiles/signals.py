from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile = Profile.objects.create(
            user=instance,
            first_name=instance.first_name or '',
            last_name=instance.last_name or '',
        )


@receiver(post_save, sender=User)
def sync_user_to_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        profile = instance.profile
        if instance.first_name != profile.first_name or instance.last_name != profile.last_name:
            profile.first_name = instance.first_name or ''
            profile.last_name = instance.last_name or ''
            profile.save(update_fields=['first_name', 'last_name', 'updated_at'])
