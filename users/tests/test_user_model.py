import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError


User = get_user_model()
HTTP_SUCCESS = 200


@pytest.mark.django_db()
def test_create_user(user: User) -> None:
    assert user.nickname == "test_user"
    assert user.email == "test@example.com"
    assert user.is_staff is False
    assert user.is_superuser is False
    assert user.check_password(user.plain_password) is True
    created_user = User.objects.filter(email="test@example.com").first()
    assert created_user is not None


@pytest.mark.django_db()
def test_create_superuser(admin_user: User) -> None:
    assert admin_user.nickname == "admin"
    assert admin_user.email == "admin@example.com"
    assert admin_user.is_staff is True
    assert admin_user.is_superuser is True
    assert admin_user.check_password(admin_user.plain_password) is True
    created_user = User.objects.filter(email="admin@example.com").first()
    assert created_user is not None


@pytest.mark.django_db()
def test_create_user_missing_email(generated_password: str) -> None:
    with pytest.raises(ValueError, match="Users must have an email address"):
        User.objects.create_user(email="", nickname="nickname", password=generated_password)


@pytest.mark.django_db()
def test_create_superuser_missing_email(generated_password: str) -> None:
    with pytest.raises(ValueError, match="Users must have an email address"):
        User.objects.create_superuser(email="", nickname="admin", password=generated_password)


@pytest.mark.django_db()
def test_create_superuser_not_staff(generated_password: str) -> None:
    with pytest.raises(ValueError, match="Superuser must have is_staff=True."):
        User.objects.create_superuser(
            email="admin@example.com",
            nickname="admin",
            password=generated_password,
            is_staff=False,
        )


@pytest.mark.django_db()
def test_create_superuser_not_superuser(generated_password: str) -> None:
    with pytest.raises(ValueError, match="Superuser must have is_superuser=True."):
        User.objects.create_superuser(
            email="admin@example.com",
            nickname="admin",
            password=generated_password,
            is_superuser=False,
        )


def test_login_user_view_get(client: Client) -> None:
    response = client.get(reverse_lazy("login"))
    assert response.status_code == HTTP_SUCCESS
    assert b"Log in" in response.content


@pytest.mark.django_db()
def test_nickname_is_null(user):
    with pytest.raises(IntegrityError):
        user.nickname = None
        user.save()


@pytest.mark.django_db()
def test_no_nickname_user_create():
    with pytest.raises(ValidationError):
        user_1 = User.objects.create(email="john@doe.com")
        user_1.clean_fields()


@pytest.mark.django_db()
def test_user_signals():
    user_1 = User.objects.create(nickname="User1", email="user@bbb.com")
    user_2 = User.objects.create(nickname="User2", email="user@aaa.com")
    assert user_1.nickname == "User1"
    assert user_2.nickname == "User2"
    assert user_1.email == "user@bbb.com"
    assert user_2.email == "user@aaa.com"
    assert user_1.profile
    assert user_2.profile
    assert user_1.user_settings
    assert user_2.user_settings
