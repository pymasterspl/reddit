import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

User = get_user_model()


@pytest.fixture()
def register_url() -> str:
    return reverse("register")


@pytest.mark.django_db()
def test_registration_page_loads_correctly(client: Client, register_url: str) -> None:
    response = client.get(register_url)
    assert response.status_code == 200
    assert "users/registration.html" in [t.name for t in response.templates]


@pytest.mark.django_db()
def test_registration_form_valid_data(
        client: Client,
        user_model: type[User],
        register_url: str,
) -> None:
    data: dict = {
        "username": "test_user",
        "email": "testuser@example.com",
        "password1": "Pass2712!",
        "password2": "Pass2712!",
    }
    assert not user_model.objects.filter(email="testuser@example.com").exists()
    response = client.post(register_url, data)
    assert response.status_code == 302
    assert response.url == reverse("home-page")
    assert user_model.objects.filter(email="testuser@example.com").exists()


@pytest.mark.django_db()
def test_registration_form_missing_data(client: Client, user_model: type[User], register_url: str) -> None:
    data: dict = {
        "username": "",
        "email": "",
        "password1": "",
        "password2": "",
    }
    response = client.post(register_url, data)
    assert response.status_code == 200
    assert "users/registration.html" in [t.name for t in response.templates]
    assert not user_model.objects.filter(email="").exists()
    form_errors = response.context["form"].errors
    assert len(form_errors) == 4
    assert "username" in form_errors
    assert "email" in form_errors
    assert "password1" in form_errors
    assert "password2" in form_errors


@pytest.mark.django_db()
def test_registration_form_user_already_exist(
        client: Client,
        user_model: type[User],
        user: User,
        register_url: str,
        generated_password: str,
) -> None:
    data: dict = {
        "username:": user.username,
        "email": user.email,
        "password1": generated_password,
        "password2": generated_password,
    }
    assert user_model.objects.filter(email=user.email).exists()
    response = client.post(register_url, data)
    assert response.status_code == 200
    assert "users/registration.html" in [t.name for t in response.templates]
    form_errors = response.context["form"].errors
    assert len(form_errors) == 2
    assert "email" in form_errors
    assert "username" in form_errors
    assert user_model.objects.count() == 1
