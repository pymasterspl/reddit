from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import User, Profile, UserSettings
from .helpers import nickname_from_email


# Do I need other signals?

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        profile = Profile.objects.create()
        if instance.profile and instance.nickname:
            nickname = instance.profile.nickname
        else:
            nickname = nickname_from_email(User, instance)
        profile.nickname = nickname
        profile.save()
        instance.profile = profile
        instance.save()

@receiver(post_save, sender=User)
def create_user_settings(sender, instance, created, **kwargs):
    if created:
        user_settings = UserSettings.objects.create()
        instance.user_settings = user_settings
        instance.save()