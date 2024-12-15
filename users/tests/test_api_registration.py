import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from rest_framework.exceptions import ErrorDetail

User = get_user_model()


@pytest.fixture()
def register_url() -> str:
    return reverse("api-user-registration")


@pytest.mark.django_db()
def test_registration_form_valid_data(
    client: Client,
    user_model: type[User],
    generated_password: str,
    register_url: str,
) -> None:
    data: dict = {
        "email": "testuser@example.com",
        "nickname": "testuser",
        "password": "Pass2712!",
        "password2": "Pass2712!",
    }
    assert not user_model.objects.filter(email="testuser@example.com").exists()
    response = client.post(register_url, data)
    assert response.status_code == 201
    assert user_model.objects.filter(email="testuser@example.com").exists()


@pytest.mark.django_db()
def test_registration_form_missing_data(client: Client, user_model: type[User], register_url: str) -> None:
    data: dict = {
        "email": "",
        "nickname": "",
        "password": "",
        "password2": "",
    }
    response = client.post(register_url, data)
    assert response.status_code == 400
    assert not user_model.objects.filter(email="").exists()
    for key in data:
        assert isinstance(response.data[key][0], ErrorDetail)


@pytest.mark.django_db()
def test_registration_form_user_already_exist(
    client: Client,
    user_model: type[User],
    user: User,
    register_url: str,
    generated_password: str,
) -> None:
    data: dict = {
        "email": user.email,
        "nickname": user.nickname,
        "password1": generated_password,
        "password2": generated_password,
    }
    assert user_model.objects.filter(email=user.email).exists()
    response = client.post(register_url, data)
    assert response.status_code == 400
    for key in ["email", "nickname"]:
        assert isinstance(response.data[key][0], ErrorDetail)
