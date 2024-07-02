from typing import ClassVar

from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields: ClassVar[list[str]] = ["nickname", "email", "password1", "password2"]


class UserProfileForm(forms.ModelForm):
    remove_avatar = forms.BooleanField(required=False, label="Remove avatar")

    class Meta:
        model = User
        fields: ClassVar[list[str]] = ["avatar"]

        widgets: ClassVar[dict[str, any]] = {
            "avatar": forms.FileInput(attrs={"class": "form-control"}),
        }

    def save(self: "UserProfileForm", *, commit: bool = True) -> User:
        user = super().save(commit=False)
        if self.cleaned_data.get("remove_avatar"):
            user.avatar.delete(save=False)
            user.avatar = None
        if commit:
            user.save()
        return user
