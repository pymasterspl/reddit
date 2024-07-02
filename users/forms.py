from typing import ClassVar

from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import User


def validate_avatar(file: any) -> None:
    max_size_mb = settings.MAX_AVATAR_SIZE_MB
    if file.size > max_size_mb * 1024 * 1024:
        message = f"Avatar file size must be under {max_size_mb}MB"
        raise ValidationError(message)


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

    def __init__(self: "UserProfileForm", *args: any, **kwargs: dict) -> None:
        super().__init__(*args, **kwargs)
        self.fields["avatar"].validators.append(validate_avatar)

    def save(self: "UserProfileForm", *, commit: bool = True) -> User:
        user = super().save(commit=False)
        if self.cleaned_data.get("remove_avatar"):
            user.avatar.delete(save=False)
            user.avatar = None
        if commit:
            user.save()
        return user
