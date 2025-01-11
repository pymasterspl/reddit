import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture()
def api_user_url(user: User) -> str:
    return reverse("api-user", kwargs={"nickname": user.nickname})


@pytest.fixture()
def api_user_profile_url() -> str:
    return reverse("api-user-profile")


@pytest.fixture()
def api_user_settings_url() -> str:
    return reverse("api-user-settings")


@pytest.mark.django_db()
def test_api_user_valid_data_response_success(
    authenticated_client: tuple[APIClient, str, str],
    api_user_url: str,
) -> None:
    client, _, _ = authenticated_client
    response = client.get(api_user_url)
    assert response.status_code == 200
    assert response.data["nickname"] == "test_user"
    assert response.data["email"] == "test@example.com"


@pytest.mark.django_db()
def test_api_user_invalid_nickname_response_failed(
    authenticated_client: tuple[APIClient, str, str],
) -> None:
    client, _, _ = authenticated_client
    response = client.get(reverse("api-user", kwargs={"nickname": "test"}))
    assert response.status_code == 404


@pytest.mark.django_db()
def test_api_user_unauthenticated_user_response_failed(
    client: Client, user_credentials: tuple[APIClient, str, str], api_user_url: str
) -> None:
    response = client.get(api_user_url)
    assert response.status_code == 401
    assert isinstance(response.data["detail"], ErrorDetail)


@pytest.mark.django_db()
def test_api_user_profile_valid_data_response_success(
    authenticated_client: tuple[APIClient, str, str], api_user_profile_url: str, user: User
) -> None:
    client, _, _ = authenticated_client
    response = client.get(api_user_profile_url)
    assert response.status_code == 200
    assert response.data == {
        "id": user.profile.id,
        "bio": user.profile.bio,
        "is_nsfw": user.profile.is_nsfw,
        "is_followable": user.profile.is_followable,
        "is_content_visible": user.profile.is_content_visible,
        "is_communities_visible": user.profile.is_communities_visible,
        "comment_karma": user.profile.comment_karma,
        "post_karma": user.profile.post_karma,
        "gold_awards": user.profile.gold_awards,
        "gender": user.profile.gender,
        "avatar": user.profile.avatar,
        "banner": user.profile.banner,
        "user": user.id,
    }


@pytest.mark.django_db()
def test_patch_api_user_profile_valid_data_response_success(
    authenticated_client: tuple[APIClient, str, str], api_user_profile_url: str, user: User
) -> None:
    client, _, _ = authenticated_client
    data = {"is_followable": not user.profile.is_followable}
    response = client.patch(api_user_profile_url, data=data)
    assert response.status_code == 200
    assert response.data == {
        "id": user.profile.id,
        "bio": user.profile.bio,
        "is_nsfw": user.profile.is_nsfw,
        "is_followable": not user.profile.is_followable,
        "is_content_visible": user.profile.is_content_visible,
        "is_communities_visible": user.profile.is_communities_visible,
        "comment_karma": user.profile.comment_karma,
        "post_karma": user.profile.post_karma,
        "gold_awards": user.profile.gold_awards,
        "gender": user.profile.gender,
        "avatar": user.profile.avatar,
        "banner": user.profile.banner,
        "user": user.id,
    }


@pytest.mark.django_db()
def test_api_user_profile_unauthenticated_user_response_failed(
    client: Client, user_credentials: tuple[APIClient, str, str], api_user_profile_url: str
) -> None:
    response = client.post(api_user_profile_url)
    assert response.status_code == 401
    assert isinstance(response.data["detail"], ErrorDetail)


@pytest.mark.django_db()
def test_api_user_settings_valid_data_response_success(
    authenticated_client: tuple[APIClient, str, str], api_user_settings_url: str, user: User
) -> None:
    client, _, _ = authenticated_client
    response = client.get(api_user_settings_url)
    assert response.status_code == 200
    assert response.data == {
        "id": user.usersettings.id,
        "content_lang": user.usersettings.content_lang,
        "location": user.usersettings.location,
        "is_beta": user.usersettings.is_beta,
        "revert_to_old_reddit": user.usersettings.revert_to_old_reddit,
        "is_over_18": user.usersettings.is_over_18,
        "user": user.id,
    }


@pytest.mark.django_db()
def test_patch_api_user_settings_valid_data_response_success(
    authenticated_client: tuple[APIClient, str, str], api_user_settings_url: str, user: User
) -> None:
    client, _, _ = authenticated_client
    data = {"is_beta": not user.usersettings.is_beta}
    response = client.patch(api_user_settings_url, data=data)
    assert response.status_code == 200
    assert response.data["is_beta"]
    assert response.data == {
        "id": user.usersettings.id,
        "content_lang": user.usersettings.content_lang,
        "location": user.usersettings.location,
        "is_beta": not user.usersettings.is_beta,
        "revert_to_old_reddit": user.usersettings.revert_to_old_reddit,
        "is_over_18": user.usersettings.is_over_18,
        "user": user.id,
    }


@pytest.mark.django_db()
def test_api_user_settings_unauthenticated_user_response_failed(
    client: Client, user_credentials: tuple[APIClient, str, str], api_user_settings_url: str
) -> None:
    response = client.post(api_user_settings_url)
    assert response.status_code == 401
    assert isinstance(response.data["detail"], ErrorDetail)
