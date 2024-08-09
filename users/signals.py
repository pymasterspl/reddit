from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import User, Profile, UserSettings
from .helpers import nickname_from_email


# Do I need other signals?

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created or not instance.profile:
        instance.profile = Profile.objects.create()
        instance.save()
        

@receiver(post_save, sender=User)
def create_user_settings(sender, instance, created, **kwargs):
    if created or not instance.user_settings:
        instance.user_settings = UserSettings.objects.create()
        instance.save() 