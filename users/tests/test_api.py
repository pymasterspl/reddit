from django.urls import reverse
import pytest
# from conftest import user

pytestmark = pytest.mark.django_db


def test_login(api_client, user):
    data = {"email": user.email, "password": user.plain_password}
    response = api_client.post(reverse("rest_login"), data)
    assert response.status_code == 200
    assert "key" in response.data


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

