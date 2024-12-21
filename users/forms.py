from typing import ClassVar
from django import forms
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from rest_framework.fields import ImageField
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

    def validate_file_size(self: "UserProfileForm", file: any, max_size: int, field_name: str) -> None:
        if file and file.size > max_size * 1024:
            msg = f"{field_name} file size should not exceed {max_size}"
            raise ValidationError(msg)

    def clean_banner(self: "UserProfileForm") -> ImageField:
        banner = self.cleaned_data.get("banner")
        self.validate_file_size(banner, settings.MAX_BANNER_SIZE_KB, "Banner")
        return banner

    def clean_avatar(self: "UserProfileForm") -> ImageField:
        avatar = self.cleaned_data.get("avatar")
        self.validate_file_size(avatar, settings.MAX_AVATAR_SIZE_MB * 1024, "Avatar")
        return avatar


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


class ConfirmDeleteAccountForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Confirm your password"}),
        label="")

    def __init__(self, user: User, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_password(self) -> str:
        password = self.cleaned_data.get("password")
        if not authenticate(username=self.user.email, password=password):
            raise forms.ValidationError("Incorrect password.")
        return password
