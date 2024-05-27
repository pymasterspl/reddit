from typing import ClassVar

from django.contrib.auth.forms import UserCreationForm

from .models import User


class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields: ClassVar[list[str]] = ["email", "password1", "password2"]
