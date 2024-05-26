from collections.abc import Callable

import pytest
from django.test import Client
from django.urls import reverse


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
        user_model: Callable,
        generated_password: str,
        register_url: str,
) -> None:
    data: dict = {
        "email": "testuser@example.com",
        "password1": "Pass2712!",
        "password2": "Pass2712!",
    }
    response = client.post(register_url, data)
    assert response.status_code == 302
    assert response.url == reverse("home-page")
    assert user_model.objects.filter(email="testuser@example.com").exists()


@pytest.mark.django_db()
def test_registration_form_invalid_data(client: Client, user_model: Callable, register_url: str) -> None:
    data: dict = {
        "email": "testuser@example.com",
        "password1": "TestPassword123",
        "password2": "DifferentPassword123",
    }
    response = client.post(register_url, data)
    assert response.status_code == 200
    assert "users/registration.html" in [t.name for t in response.templates]
    assert not user_model.objects.filter(email="testuser@example.com").exists()
    assert "The two password fields didn’t match." in response.content.decode()


@pytest.mark.django_db()
def test_registration_form_missing_data(client: Client, user_model: Callable, register_url: str) -> None:
    data: dict = {
        "email": "",
        "password1": "",
        "password2": "",
    }
    response = client.post(register_url, data)
    assert response.status_code == 200
    assert "users/registration.html" in [t.name for t in response.templates]
    assert not user_model.objects.filter(email="").exists()
    assert "This field is required." in response.content.decode()
