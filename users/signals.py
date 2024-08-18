from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile, User, UserSettings


@receiver(post_save, sender=User)
def create_profile(sender: type, instance: User, created: bool, **kwargs: dict) -> None:  # noqa: ARG001, FBT001
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def create_usersettings(sender: type, instance: User, created: bool, **kwargs: dict) -> None:  # noqa: ARG001, FBT001
    if created:
        UserSettings.objects.create(user=instance)
