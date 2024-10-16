from typing import ClassVar

from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import User, Profile, UserSettings


def validate_avatar(file: any) -> None:
    max_size_mb = settings.MAX_AVATAR_SIZE_MB
    if file.size > max_size_mb * 1024 * 1024:
        message = f"Avatar file size must be under {max_size_mb}MB"
        raise ValidationError(message)


class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields: ClassVar[list[str]] = ["nickname", "email", "password1", "password2"]


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['nickname']


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'bio',
            'avatar',
            'gender',
            'is_nsfw',
            'is_followable',
            'is_content_visible',
            'is_communities_visible',
        ]


class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = [
            'content_lang',
            'location',
            'is_beta',
            'is_over_18',
            'revert_to_old_reddit',
        ]
