import secrets
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.core.exceptions import ValidationError
from social_core.strategy import BaseStrategy

User = get_user_model()


def generate_secure_random_digits(length: int = 6) -> str:
    return "".join([str(secrets.randbelow(10)) for _ in range(length)])


def associate_by_email(
    strategy: BaseStrategy,  # noqa: ARG001
    details: dict,
    backend: BaseBackend,  # noqa: ARG001
    user: User = None,
    *args: tuple,  # noqa: ARG001
    **kwargs: dict[str, Any],  # noqa: ARG001
) -> User:
    """Associates an existing user with a social account if the email matches."""
    if user:
        return None

    email = details.get("email")
    if email:
        try:
            existing_user = User.objects.get(email=email)
        except User.DoesNotExist:
            pass
        else:
            return {"user": existing_user}
    else:
        error_message = "Email address is required to authenticate."
        raise ValidationError(error_message)


def set_default_nickname(
    strategy: BaseStrategy,  # noqa: ARG001
    details: dict,
    user: User = None,
    *args: tuple,  # noqa: ARG001
    **kwargs: dict[str, Any],  # noqa: ARG001
) -> None:
    if not user:
        details["nickname"] = details.get("email").split("@")[0][:138] + generate_secure_random_digits()
