from django.urls import reverse
import pytest
import dj_rest_auth.views
from rest_framework.test import force_authenticate
from django.contrib.sessions.middleware import SessionMiddleware
from users.models import User


pytestmark = pytest.mark.django_db


PREFIX = "http://testserver"



@pytest.fixture()
def user_data(create_avatar):
    return {
        "nickname": "userin",
        "email": "userin@user.pl",
        "avatar": create_avatar,
    }


@pytest.fixture()
def create_usersettings_data():
    def _usersettings_data(user):
        return {
            "is_beta": True,
            "is_over_18": False,
            "content_lang": "en",
            "user": user.id,
            "location": "UA",
        }
    return _usersettings_data

def test_login_and_logout(api_client, user, api_request_factory):
    """
    Test:
    logges in and saves token
    checks if user with token can access auth protected endpoint - he should
    logges out
    checks if user with token can acess auth protected endpoint - he shouldn't
    """
    data = {"email": user.email, "password": user.plain_password}
    response = api_client.post(reverse("rest_login"), data)
    token = f"Token {response.data['key']}"
    headers = {"HTTP_AUTHORIZATION": token}
    request = api_request_factory.get(reverse("rest_user_details"), format="json", **headers)
    response_protected = dj_rest_auth.views.UserDetailsView.as_view()(request)
    assert response.status_code == 200
    assert "key" in response.data
    assert response_protected.status_code == 200
    logout_request = api_request_factory.post(reverse("rest_logout"), format="json", **headers)
    
    # adding session to request as logout has to flush existing session and requires session attribute
    middleware = SessionMiddleware(lambda x: None)
    middleware.process_request(logout_request)
    logout_request.session.save()

    logout_response = dj_rest_auth.views.LogoutView.as_view()(logout_request)
    assert logout_response.status_code == 200
    request = api_request_factory.get(reverse("rest_user_details"), format="json", **headers)
    response_protected = dj_rest_auth.views.UserDetailsView.as_view()(request)
    assert response_protected.status_code == 401

# TODO 404 for these, zły token

def test_user_detail(api_client, user):
    assert user.profile
    assert user.usersettings
    api_client.force_authenticate(user)
    response = api_client.get(reverse("rest_user_details"))
    assert response.status_code == 200
    assert response.data["profile"] == user.profile.id
    assert response.data["usersettings"] == user.usersettings.id
    assert response.data["nickname"] == user.nickname
    assert response.data["email"] == user.email
    assert "avatar" in response.data
    assert "is_online" in response.data
    assert "last_activity_ago" in response.data
    assert "last_activity" in response.data


def test_user_detail_put(api_client, user, profile, user_data):
    api_client.force_authenticate(user)
    profile(user)
    response = api_client.put(reverse("rest_user_details"), user_data, format="multipart")
    avatar_name = user_data["avatar"].name.split(".")[0]
    assert response.status_code == 200
    assert user.nickname == user_data["nickname"]
    assert user.email == user_data["email"]
    assert avatar_name in user.avatar.name


@pytest.mark.parametrize("missing_field", ["nickname", "email"])
def test_user_detail_put_missing_field(api_client, user_data, missing_field, user, profile):
    api_client.force_authenticate(user)
    profile(user)
    del user_data[missing_field]
    response = api_client.put(reverse("rest_user_details"), user_data, format="multipart")
    assert response.status_code == 400


@pytest.mark.parametrize("changed_field", ["nickname", "email"])
def test_user_detail_patch_field(api_client, changed_field, user, user_data):
    api_client.force_authenticate(user)
    data = {changed_field: user_data[changed_field]}
    response = api_client.patch(reverse("rest_user_details"), data, "json")
    assert response.status_code == 200
    assert getattr(user, changed_field)== user_data[changed_field]


def test_user_detail_patch_avatar(api_client, user, user_data):
    api_client.force_authenticate(user)
    avatar_in_data = user_data["avatar"]
    avatar_in_data.name = "some_name.jpg"
    data = {"avatar": avatar_in_data}
    response = api_client.patch(reverse("rest_user_details"), data, format="multipart")
    assert response.status_code == 200
    assert user.avatar
    assert "some_name" in user.avatar.name
    

def test_user_detail_check_if_protected(api_client):
    response = api_client.get(reverse("rest_user_details"), format="json")
    assert response.status_code == 401

def test_user_detail_fake_token_check_if_protected(api_request_factory):
    fake_token_str = "Token 2f4b1c3e6d7a8b9c0e1d2a3b4c5e6f7g8h9i0j1k2"
    headers = {"HTTP_AUTHORIZATION": fake_token_str}
    request = api_request_factory.get(reverse("rest_user_details"), format="json", **headers)
    response = dj_rest_auth.views.UserDetailsView.as_view()(request)
    assert response.status_code == 401


def test_my_profile_check_if_protected(api_client, user):
    response = api_client.get(reverse("my_profile"), format="json")
    assert response.status_code == 401


def test_profile_check_if_protected(api_client, user):
    response = api_client.get(reverse("profile", kwargs={"pk": user.profile.pk}), format="json")
    assert response.status_code == 401

    
def assert_profile_fields(data, profile):
    assert data["id"] == profile.id
    assert data["nickname"] == profile.user.nickname
    assert data["gender"] == profile.gender
    assert data["bio"] == profile.bio
    assert data["avatar"] == PREFIX + profile.user.avatar.url
    assert data["post_karma"] == profile.post_karma
    assert data["comment_karma"] == profile.comment_karma
    assert data["is_nsfw"] == profile.is_nsfw
    assert data["is_followable"] == profile.is_followable
    assert data["is_content_visible"] == profile.is_content_visible
    assert data["is_communities_visible"] == profile.is_communities_visible

def test_my_profile(api_client, user_with_everything):
    api_client.force_authenticate(user_with_everything)
    response = api_client.get(reverse("my_profile"))
    assert response.status_code == 200
    assert_profile_fields(response.data, user_with_everything.profile)


def test_profile(api_client, another_user, user_with_everything):
    api_client.force_authenticate(another_user)
    response = api_client.get(reverse("profile", kwargs={"pk": user_with_everything.profile.pk}))
    assert response.status_code == 200
    assert_profile_fields(response.data, user_with_everything.profile)


def test_my_usersettings(api_client, user, usersettings):
    api_client.force_authenticate(user)
    settings_obj = usersettings(user)
    response = api_client.get(reverse("my_user_settings"), format="json")
    assert response.status_code == 200
    assert settings_obj.user.id == response.data["user"]
    assert settings_obj.is_beta == response.data["is_beta"]
    assert settings_obj.is_over_18 == response.data["is_over_18"]
    assert settings_obj.content_lang == response.data["content_lang"]
    assert settings_obj.location == response.data["location"]


def test_my_usersettings_put(api_client, user, create_usersettings_data):
    api_client.force_authenticate(user)
    settings_data = create_usersettings_data(user)
    response = api_client.put(reverse("my_user_settings"), settings_data, format="json")
    print("x", response.data)
    assert response.status_code == 200
    assert settings_data["user"] == user.id
    assert settings_data["content_lang"] == user.usersettings.content_lang
    assert settings_data["is_over_18"] == user.usersettings.is_over_18
    assert settings_data["location"] == user.usersettings.location
    assert settings_data["is_beta"] == user.usersettings.is_beta


@pytest.mark.parametrize("changed_field", ["content_lang", "is_over_18", "location", "is_beta"])
def test_my_usersettings_patch(changed_field, api_client, user, create_usersettings_data):
    api_client.force_authenticate(user)
    settings_data = create_usersettings_data(user)
    data = {changed_field: settings_data[changed_field]}
    response = api_client.patch(reverse("my_user_settings"), data, format="json")
    assert response.status_code == 200
    assert getattr(user.usersettings, changed_field)== settings_data[changed_field]


def test_my_usersettings_if_protected(api_client, user, usersettings):
    usersettings(user)
    response = api_client.get(reverse("my_user_settings"))
    assert response.status_code == 401