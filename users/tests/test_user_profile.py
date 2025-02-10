import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from core.models import Post
from users.models import User

user = get_user_model()


@pytest.mark.django_db()
def test_user_profile_correct_user(client: Client, user: User) -> None:
    url = reverse("user_public_profile", kwargs={"nickname": user.nickname})
    response = client.get(url)

    assert response.status_code == 200
    assert user.nickname in response.content.decode()


@pytest.mark.django_db()
def test_user_profile_no_exist_user(client: Client) -> None:
    url = reverse("user_public_profile", kwargs={"nickname": "nonexistent"})
    response = client.get(url)

    assert response.status_code == 404


@pytest.mark.django_db()
def test_user_profile_displays_bio_and_posts(client: Client, user: User, post: Post) -> None:
    url = reverse("user_public_profile", kwargs={"nickname": user.nickname})
    response = client.get(url)
    content = response.content.decode()

    assert response.status_code == 200
    assert user.profile.bio in content
    assert post.title in content
    assert post.content[:100] in content
