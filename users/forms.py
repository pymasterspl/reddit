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


class EmailChangeForm(forms.Form):
    old_email = forms.EmailField(required=True)
    new_email = forms.EmailField(required=True)
    new_email_confirmation = forms.EmailField(required=True)

    def __init__(self: "EmailChangeForm", user: User, *args: str, **kwargs: str) -> None:
        super().__init__(*args, **kwargs)
        self.user = user

    def is_valid(self: "EmailChangeForm") -> bool:
        valid = super().is_valid()
        if not valid:
            return valid
        if self.cleaned_data.get("old_email") != self.user.email:
            error_msg = "Provided old email is incorrect!"
            self.add_error("old_email", error_msg)
            return False
        email1 = self.cleaned_data.get("new_email")
        email2 = self.cleaned_data.get("new_email_confirmation")
        if email1 != email2:
            error_msg = "Provided emails are not the same"
            self.add_error("new_email", error_msg)
            return False
        if User.objects.filter(email=email1).exists():
            error_msg = "This email is already in use"
            self.add_error("new_email", error_msg)
            return False
        return True

class Enable2FAForm:
    pass