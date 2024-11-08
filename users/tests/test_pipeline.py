import hashlib
from unittest.mock import Mock

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from users.pipeline import associate_by_email, set_default_nickname

User = get_user_model()


@pytest.mark.django_db()
def test_associate_by_email_existing_user() -> None:
    email = "existing@example.com"
    nickname = "ExistingNick"
    existing_user = User.objects.create(email=email, nickname=nickname)
    details = {"email": email}

    result = associate_by_email(strategy=Mock(), details=details, backend=Mock(), user=None)

    assert result["user"] == existing_user
    assert result["user"].nickname == nickname


@pytest.mark.django_db()
def test_associate_by_email_no_user_found() -> None:
    # Prepare the data with a non-existing email
    details = {"email": "newuser@example.com"}

    # Run the function
    result = associate_by_email(strategy=Mock(), details=details, backend=Mock(), user=None)

    # Assert that the function returns None when no user is found
    assert result is None


@pytest.mark.django_db()
def test_associate_by_email_no_email_provided() -> None:
    # Prepare the data with missing email
    details = {}

    # Run the function and expect an exception
    with pytest.raises(ValidationError) as excinfo:
        associate_by_email(strategy=Mock(), details=details, backend=Mock(), user=None)

    # Assert that the exception message matches
    assert excinfo.value.messages[0] == "Email address is required to authenticate."


@pytest.mark.django_db()
@pytest.mark.parametrize("email_value", [None, ""])
def test_associate_by_email_invalid_email(email_value: str) -> None:
    details = {"email": email_value} if email_value is not None else {}
    with pytest.raises(ValidationError) as excinfo:
        associate_by_email(strategy=Mock(), details=details, backend=Mock(), user=None)
    assert excinfo.value.messages[0] == "Email address is required to authenticate."


@pytest.mark.django_db()
def test_associate_by_email_user_already_authenticated() -> None:
    # Setup: Create an existing user
    email = "authenticated@example.com"
    existing_user = User.objects.create(email=email)

    # Run the function with an already authenticated user
    result = associate_by_email(strategy=Mock(), details={"email": email}, backend=Mock(), user=existing_user)

    # Assert that the function returns None as no association is needed
    assert result is None


@pytest.mark.django_db()
def test_set_default_nickname_with_no_nickname() -> None:
    # Prepare the data with no nickname
    details = {"email": "newuser@example.com"}

    # Run the function with no user provided (indicating a new user)
    set_default_nickname(strategy=Mock(), details=details, user=None)

    # Assert that the nickname in details is set to the email
    assert details["nickname"][:10] in str(hashlib.sha256(b"newuser@example.com").hexdigest())


@pytest.mark.django_db()
def test_set_default_nickname_with_authenticated_user() -> None:
    # Prepare the data
    details = {"email": "authenticated@example.com"}

    # Run the function with an authenticated user
    set_default_nickname(strategy=Mock(), details=details, user=Mock())

    # Assert that nickname is not set in details
    assert "nickname" not in details
