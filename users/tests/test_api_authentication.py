import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from rest_framework.exceptions import ErrorDetail
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

User = get_user_model()


@pytest.fixture()
def api_login_url() -> str:
    return reverse("api-user-login")


@pytest.fixture()
def api_logout_url() -> str:
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
    client: Client, user: User, api_login_url: str, token_refresh_url: str, user_credentials: dict[str, str]
) -> None:
    response = client.post(api_login_url, user_credentials)
    access_token = response.data["access"]
    refresh_token = response.data["refresh"]
    response = client.post(token_refresh_url, {"refresh": refresh_token})
    assert response.status_code == 200
    assert "access" in response.data
    assert response.data["access"] != access_token


@pytest.mark.django_db()
def test_refresh_token_invalid_data_response_failed(
    client: Client, user: User, api_login_url: str, token_refresh_url: str, user_credentials: dict[str, str]
) -> None:
    client.post(api_login_url, user_credentials)
    response = client.post(token_refresh_url, {"refresh": "123"})
    assert response.status_code == 401
    assert "access" not in response.data
    assert "refresh" not in response.data


@pytest.mark.django_db()
def test_api_logout_valid_data_response_success(
    client: Client, user: User, api_login_url: str, api_logout_url: str, user_credentials: dict[str, str]
) -> None:
    login_response = client.post(api_login_url, user_credentials)
    refresh_token = login_response.data["refresh"]
    access_token = login_response.data["access"]
    headers = {"HTTP_AUTHORIZATION": f"Bearer {access_token}"}
    response = client.post(api_logout_url, {"refresh": refresh_token}, **headers)
    assert response.status_code == 202
    assert BlacklistedToken.objects.all().first().token.token == refresh_token
    assert response.data["message"] == "Logged out successfully"


@pytest.mark.django_db()
def test_api_logout_invalid_data_response_failed(
    client: Client, user: User, api_login_url: str, api_logout_url: str, user_credentials: dict[str, str]
) -> None:
    login_response = client.post(api_login_url, user_credentials)
    access_token = login_response.data["access"]
    headers = {"HTTP_AUTHORIZATION": f"Bearer {access_token}"}
    response = client.post(api_logout_url, {"refresh": "123"}, **headers)
    assert response.status_code == 400
    assert response.data["message"] == "Token is invalid or expired"


@pytest.mark.django_db()
def test_api_logout_unauthenticated_user_response_failed(
    client: Client, user: User, api_login_url: str, api_logout_url: str, user_credentials: dict[str, str]
) -> None:
    client.post(api_login_url, user_credentials)
    response = client.post(api_logout_url, {"refresh": "123"})
    assert response.status_code == 401
    assert isinstance(response.data["detail"], ErrorDetail)


@pytest.mark.django_db()
def test_refresh_token_invalid_format_response_failed(
    client: Client, user: User, api_login_url: str, token_refresh_url: str, user_credentials: dict[str, str]
) -> None:
    client.post(api_login_url, user_credentials)
    response = client.post(token_refresh_url, {"refresh": "not.a.valid.jwt.format"})
    assert response.status_code == 401
    assert "access" not in response.data


@pytest.mark.django_db()
def test_refresh_token_revoked_response_failed(
    client: Client, user: User, api_login_url: str, token_refresh_url: str, user_credentials: dict[str, str]
) -> None:
    login_response = client.post(api_login_url, user_credentials)
    refresh_token = login_response.data["refresh"]

    token = OutstandingToken.objects.get(token=refresh_token)
    BlacklistedToken.objects.create(token=token)

    response = client.post(token_refresh_url, {"refresh": refresh_token})
    assert response.status_code == 401
    assert "access" not in response.data
