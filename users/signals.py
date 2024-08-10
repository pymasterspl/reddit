from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile, User, UserSettings


@receiver(post_save, sender=User)
def create_profile(sender: type, instance: User, created: bool, **kwargs: dict) -> None:  # noqa: ARG001, FBT001
    if created or not instance.profile:
        instance.profile = Profile.objects.create()
        instance.save()


@receiver(post_save, sender=User)
def create_user_settings(sender: type, instance: User, created: bool, **kwargs: dict) -> None:  # noqa: ARG001, FBT001
    if created or not instance.user_settings:
        instance.user_settings = UserSettings.objects.create()
        instance.save()
