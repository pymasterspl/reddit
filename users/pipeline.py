from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.core.exceptions import ValidationError
from social_core.strategy import BaseStrategy

User = get_user_model()


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
        return None  # User is already authenticated, no need to associate

    email = details.get("email")
    if email:
        try:
            existing_user = User.objects.get(email=email)
        except User.DoesNotExist:
            pass  # If no user is found, proceed with creating a new one
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
        details["nickname"] = details.get("email")
