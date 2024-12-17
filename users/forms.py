from typing import ClassVar

from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Profile, User, UserSettings


class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields: ClassVar[list[str]] = ["nickname", "email", "password1", "password2"]


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields: ClassVar[list[str]] = ["nickname"]


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields: ClassVar[list[str]] = [
            "bio",
            "avatar",
            "banner",
            "gender",
            "is_nsfw",
            "is_followable",
            "is_content_visible",
            "is_communities_visible",
        ]


class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields: ClassVar[list[str]] = [
            "content_lang",
            "location",
            "is_beta",
            "is_over_18",
            "revert_to_old_reddit",
        ]
