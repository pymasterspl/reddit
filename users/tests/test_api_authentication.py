import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from rest_framework.exceptions import ErrorDetail
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

User = get_user_model()


@pytest.fixture()
def login_url() -> str:
    return reverse("api-user-login")


@pytest.fixture()
def logout_url() -> str:
    return reverse("api-user-logout")


@pytest.fixture()
def token_refresh_url() -> str:
    return reverse("api-token-refresh")


@pytest.fixture()
def user_credentials(user: User) -> dict[str, str]:
    return {
        "email": user.email,
        "password": user.plain_password,
    }


@pytest.mark.django_db()
def test_login_valid_data_response_success(
    client: Client, user: User, login_url: str, user_credentials: dict[str, str]
) -> None:
    response = client.post(login_url, user_credentials)
    assert response.status_code == 200
    assert user.is_authenticated
    assert "access" in response.data
    assert "refresh" in response.data


@pytest.mark.django_db()
def test_login_invalid_data_response_failed(
    client: Client,
    user: User,
    login_url: str,
) -> None:
    data: dict = {
        "email": "test@mail.com",
        "password": "12345",
    }
    response = client.post(login_url, data)
    assert response.status_code == 401
    assert "access" not in response.data
    assert "refresh" not in response.data


@pytest.mark.django_db()
def test_refresh_token_valid_data_response_success(
    client: Client, user: User, login_url: str, token_refresh_url: str, user_credentials: dict[str, str]
) -> None:
    response = client.post(login_url, user_credentials)
    access_token = response.data["access"]
    refresh_token = response.data["refresh"]
    response = client.post(token_refresh_url, {"refresh": refresh_token})
    assert response.status_code == 200
    assert "access" in response.data
    assert response.data["access"] != access_token


@pytest.mark.django_db()
def test_refresh_token_invalid_data_response_failed(
    client: Client, user: User, login_url: str, token_refresh_url: str, user_credentials: dict[str, str]
) -> None:
    client.post(login_url, user_credentials)
    response = client.post(token_refresh_url, {"refresh": "123"})
    assert response.status_code == 401
    assert "access" not in response.data
    assert "refresh" not in response.data


@pytest.mark.django_db()
def test_logout_valid_data_response_success(
    client: Client, user: User, login_url: str, logout_url: str, user_credentials: dict[str, str]
) -> None:
    response = client.post(login_url, user_credentials)
    refresh_token = response.data["refresh"]
    response = client.post(logout_url, {"refresh": refresh_token})
    assert response.status_code == 202
    assert BlacklistedToken.objects.all().first().token.token == refresh_token
    assert response.data["message"] == "Logged out successfully"


@pytest.mark.django_db()
def test_logout_invalid_data_response_failed(
    client: Client, user: User, login_url: str, logout_url: str, user_credentials: dict[str, str]
) -> None:
    client.post(login_url, user_credentials)
    response = client.post(logout_url, {"refresh": "123"})
    assert response.status_code == 400
    assert response.data["message"] == "Token is invalid or expired"


@pytest.mark.django_db()
def test_logout_unauthenticated_user_response_failed(
    client: Client, user: User, login_url: str, logout_url: str, user_credentials: dict[str, str]
) -> None:
    response = client.post(logout_url, {"refresh": "123"})
    assert response.status_code == 401
    assert isinstance(response.data["detail"], ErrorDetail)
