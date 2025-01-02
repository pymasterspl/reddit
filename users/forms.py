from typing import ClassVar

from django import forms
from django.contrib.auth import authenticate
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


class ConfirmDeleteAccountForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Confirm your password"}), label=""
    )

    def __init__(self: "ConfirmDeleteAccountForm", user: User, *args: str, **kwargs: str) -> None:
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_password(self: "ConfirmDeleteAccountForm") -> str:
        password = self.cleaned_data.get("password")
        if not authenticate(username=self.user.email, password=password):
            error_message = "Incorrect password."
            raise forms.ValidationError(error_message)
        return password
