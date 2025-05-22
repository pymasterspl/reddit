import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

User = get_user_model()


@pytest.mark.django_db()
def test_api_login_valid_data_response_success(
    client: Client, user: User, api_login_url: str, user_credentials: dict[str, str]
) -> None:
    response = client.post(api_login_url, user_credentials)
    assert response.status_code == 200
    assert user.is_authenticated
    assert "access" in response.data
    assert "refresh" in response.data


@pytest.mark.django_db()
def test_api_login_invalid_data_response_failed(
    client: Client,
    user: User,
    api_login_url: str,
) -> None:
    data: dict = {
        "email": "test@mail.com",
        "password": "12345",
    }
    response = client.post(api_login_url, data)
    assert response.status_code == 401
    assert "access" not in response.data
    assert "refresh" not in response.data


@pytest.mark.django_db()
def test_api_login_inactive_account_response_failed(
    client: Client, user: User, api_login_url: str, api_register_url: str
) -> None:
    data: dict = {
        "email": "testuser@example.com",
        "nickname": "testuser",
        "password": "Pass2712!",
        "password2": "Pass2712!",
    }
    client.post(api_register_url, data)
    response = client.post(api_login_url, {"email": data["email"], "password": data["password"]})
    assert response.status_code == 401
    assert "access" not in response.data
    assert "refresh" not in response.data


@pytest.mark.django_db()
def test_refresh_token_valid_data_response_success(
    authenticated_client: tuple[APIClient, str, str], token_refresh_url: str
) -> None:
    client, access_token, refresh_token = authenticated_client
    response = client.post(token_refresh_url, {"refresh": refresh_token})
    assert response.status_code == 200
    assert "access" in response.data
    assert response.data["access"] != access_token


@pytest.mark.django_db()
def test_refresh_token_invalid_data_response_failed(
    authenticated_client: tuple[APIClient, str, str], token_refresh_url: str
) -> None:
    client, _, _ = authenticated_client
    response = client.post(token_refresh_url, {"refresh": "123"})
    assert response.status_code == 401
    assert "access" not in response.data
    assert "refresh" not in response.data


@pytest.mark.django_db()
def test_api_logout_valid_data_response_success(
    authenticated_client: tuple[APIClient, str, str], api_logout_url: str
) -> None:
    client, _, refresh_token = authenticated_client
    response = client.post(api_logout_url, {"refresh": refresh_token})
    assert response.status_code == 202
    assert BlacklistedToken.objects.filter(token__token=refresh_token).exists()
    assert response.data["message"] == "Logged out successfully"


@pytest.mark.django_db()
def test_api_logout_invalid_data_response_failed(
    authenticated_client: tuple[APIClient, str, str], api_logout_url: str
) -> None:
    client, _, _ = authenticated_client
    response = client.post(api_logout_url, {"refresh": "123"})
    assert response.status_code == 400
    assert response.data["message"] == "Token is invalid"


@pytest.mark.django_db()
def test_api_logout_unauthenticated_user_response_failed(
    client: Client, authenticated_client: tuple[APIClient, str, str], api_logout_url: str
) -> None:
    _, _, refresh_token = authenticated_client
    response = client.post(api_logout_url, {"refresh": refresh_token})
    assert response.status_code == 401
    assert isinstance(response.data["detail"], ErrorDetail)


@pytest.mark.django_db()
def test_refresh_token_invalid_format_response_failed(
    authenticated_client: tuple[APIClient, str, str], token_refresh_url: str
) -> None:
    client, _, _ = authenticated_client
    response = client.post(token_refresh_url, {"refresh": "not.a.valid.jwt.format"})
    assert response.status_code == 401
    assert "access" not in response.data


@pytest.mark.django_db()
def test_refresh_token_revoked_response_failed(
    authenticated_client: tuple[APIClient, str, str], token_refresh_url: str
) -> None:
    client, _, refresh_token = authenticated_client
    token = OutstandingToken.objects.get(token=refresh_token)
    BlacklistedToken.objects.create(token=token)
    response = client.post(token_refresh_url, {"refresh": refresh_token})
    assert response.status_code == 401
    assert "access" not in response.data
    assert "access" not in response.data
