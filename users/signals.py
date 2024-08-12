from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver

from .models import Profile, User, UserSettings


@receiver(pre_save, sender=User)
def create_profile(sender: type, instance: User, **kwargs: dict) -> None:  # noqa: ARG001, FBT001
    if not instance.pk:
        instance.profile = Profile.objects.create()
        


@receiver(pre_save, sender=User)
def create_user_settings(sender: type, instance: User, **kwargs: dict) -> None:  # noqa: ARG001, FBT001
    if not instance.pk:
        instance.user_settings = UserSettings.objects.create()
        

@receiver(pre_delete, sender=User)
def delete_profile_and_user_settings(sender: type, instance: User, **kwargs: dict) -> None:
    if instance.profile:
        instance.profile.delete()
    if instance.user_settings:
        instance.user_settings.delete()
