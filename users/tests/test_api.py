from unittest.mock import patch
from django.urls import reverse
import pytest
import dj_rest_auth.views
from rest_framework.test import force_authenticate
from django.contrib.sessions.middleware import SessionMiddleware


pytestmark = pytest.mark.django_db


PREFIX = "http://testserver"

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