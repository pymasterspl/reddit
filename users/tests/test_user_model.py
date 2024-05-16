import secrets
import string

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse_lazy

User = get_user_model()

HTTP_SUCCESS = 200


def generate_random_password(length: int = 12) -> str:
    characters = string.ascii_letters + string.digits + string.punctuation
    secure_random = secrets.SystemRandom()
    return "".join(secure_random.choice(characters) for _ in range(length))


@pytest.fixture()
def generated_password() -> str:
    return generate_random_password()


@pytest.fixture()
def user(generated_password: str) -> User:
    user = User.objects.create_user(email="test@example.com", password=generated_password)
    user.plain_password = generated_password
    return user


@pytest.fixture()
def admin_user(generated_password: str) -> User:
    admin_user = User.objects.create_superuser(email="admin@example.com", password=generated_password)
    admin_user.plain_password = generated_password
    return admin_user


@pytest.fixture()
def client() -> Client:
    return Client()


@pytest.mark.django_db()
def test_create_user(user: User) -> None:
    assert user.email == "test@example.com"
    assert user.is_staff is False
    assert user.is_superuser is False
    assert user.check_password(user.plain_password) is True


@pytest.mark.django_db()
def test_create_superuser(admin_user: User) -> None:
    assert admin_user.email == "admin@example.com"
    assert admin_user.is_staff is True
    assert admin_user.is_superuser is True
    assert admin_user.check_password(admin_user.plain_password) is True


@pytest.mark.django_db()
def test_create_user_missing_email(generated_password: str) -> None:
    with pytest.raises(ValueError, match="Users must have an email address"):
        User.objects.create_user(email="", password=generated_password)


@pytest.mark.django_db()
def test_create_superuser_missing_email(generated_password: str) -> None:
    with pytest.raises(ValueError, match="Users must have an email address"):
        User.objects.create_superuser(email="", password=generated_password)


@pytest.mark.django_db()
def test_create_superuser_not_staff(generated_password: str) -> None:
    with pytest.raises(ValueError, match="Superuser must have is_staff=True."):
        User.objects.create_superuser(email="admin@example.com", password=generated_password, is_staff=False)


@pytest.mark.django_db()
def test_create_superuser_not_superuser(generated_password: str) -> None:
    with pytest.raises(ValueError, match="Superuser must have is_superuser=True."):
        User.objects.create_superuser(email="admin@example.com", password=generated_password, is_superuser=False)


def test_login_user_view_get(client: Client) -> None:
    response = client.get(reverse_lazy("login"))
    assert response.status_code == HTTP_SUCCESS
    assert b"Log in" in response.content


@pytest.mark.django_db()
def test_login_user_view_post_success(client: Client, user: User) -> None:
    data = {"email": "test@example.com", "password": "testpassword"}
    response = client.post(reverse_lazy("login"), data=data)
    assert response.status_code == HTTP_SUCCESS


@pytest.mark.django_db()
def test_login_user_view_post_success_authenticated(client: Client, user: User) -> None:
    data = {"email": "test@example.com", "password": "testpassword"}
    response = client.post(reverse_lazy("login"), data=data)
    assert response.status_code == HTTP_SUCCESS

    user = User.objects.get(email="test@example.com")
    assert user.is_authenticated


def test_login_user_view_post_missing_credentials(client: Client) -> None:
    data = {}
    response = client.post(reverse_lazy("login"), data=data)
    assert response.status_code == HTTP_SUCCESS
