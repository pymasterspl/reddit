import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.test import Client
from django.urls import reverse_lazy

User = get_user_model()

HTTP_SUCCESS = 200


@pytest.mark.django_db()
def test_create_user(user: User) -> None:
    assert user.username == "test_user"
    assert user.email == "test@example.com"
    assert user.is_staff is False
    assert user.is_superuser is False
    assert user.check_password(user.plain_password) is True
    created_user = User.objects.filter(email="test@example.com").first()
    assert created_user is not None


@pytest.mark.django_db()
def test_create_superuser(admin_user: User) -> None:
    assert admin_user.username == "admin"
    assert admin_user.email == "admin@example.com"
    assert admin_user.is_staff is True
    assert admin_user.is_superuser is True
    assert admin_user.check_password(admin_user.plain_password) is True
    created_user = User.objects.filter(email="admin@example.com").first()
    assert created_user is not None


@pytest.mark.django_db()
def test_create_user_missing_email(generated_password: str) -> None:
    with pytest.raises(ValueError, match="Users must have an email address"):
        User.objects.create_user(username="username", email="", password=generated_password)


@pytest.mark.django_db()
def test_create_superuser_missing_email(generated_password: str) -> None:
    with pytest.raises(ValueError, match="Users must have an email address"):
        User.objects.create_superuser(username="admin", email="", password=generated_password)


@pytest.mark.django_db()
def test_create_superuser_not_staff(generated_password: str) -> None:
    with pytest.raises(ValueError, match="Superuser must have is_staff=True."):
        User.objects.create_superuser(username="admin", email="admin@example.com", password=generated_password, is_staff=False)


@pytest.mark.django_db()
def test_create_superuser_not_superuser(generated_password: str) -> None:
    with pytest.raises(ValueError, match="Superuser must have is_superuser=True."):
        User.objects.create_superuser(username="admin", email="admin@example.com", password=generated_password, is_superuser=False)


def test_login_user_view_get(client: Client) -> None:
    response = client.get(reverse_lazy("login"))
    assert response.status_code == HTTP_SUCCESS
    assert b"Log in" in response.content


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
    form = AuthenticationForm(data=data)
    form.is_valid()
    assert form.errors.get("username") == ["This field is required."]
    assert form.errors.get("password") == ["This field is required."]
