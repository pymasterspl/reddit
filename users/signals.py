from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Profile, User, UserSettings


@receiver(pre_save, sender=User)
def create_profile(sender: type, instance: User, **kwargs: dict) -> None:  # noqa: ARG001, FBT001
    if not instance.profile:
        instance.profile = Profile.objects.create()
        instance.save()


@receiver(pre_save, sender=User)
def create_user_settings(sender: type, instance: User, **kwargs: dict) -> None:  # noqa: ARG001, FBT001
    if not instance.user_settings:
        instance.user_settings = UserSettings.objects.create()
        instance.save()
