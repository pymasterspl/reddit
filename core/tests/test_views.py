import secrets
import string

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from core.models import Community, Post

pytestmark = pytest.mark.django_db

User = get_user_model()


def generate_random_password(length: int = 12) -> str:
    characters = string.ascii_letters + string.digits + string.punctuation
    return "".join(secrets.choice(characters) for _ in range(length))


@pytest.fixture()
def user(client: Client) -> User:
    password = generate_random_password()
    user = User.objects.create_user(
        email="test_user@example.com",
        nickname="TestUser",
        password=password,
    )

    client.login(email=user.email, password=user.password)
    return user


@pytest.fixture()
def community() -> Community:
    return Community.objects.create(name="Test Community", is_active=True)


@pytest.fixture()
def create_post(client: Client, user: User, community: Community) -> Post:
    client.force_login(user)
    data = {
        "community": community.pk,
        "title": "Test Post Title",
        "content": "This is a test post content.",
    }
    response = client.post(reverse("post-create"), data=data, follow=True)
    assert response.status_code == 200, (
        f"Response status code was {response.status_code}, " f"response content: {response.content}"
    )
    return Post.objects.get(title=data["title"])


def test_add_post_valid(client: Client, user: User, community: Community) -> None:
    data = {
        "community": community.pk,
        "title": "Test Post Title",
        "content": "This is a test post content.",
    }
    client.force_login(user)
    response = client.post(reverse("post-create"), data=data, follow=True)
    assert response.status_code == 200
    assert response.context["post"].author == user
    assert response.context["post"].title == data["title"]
    assert response.context["post"].content == data["content"]


def test_add_post_invalid(client: Client, user: User, community: Community) -> None:
    data = {"title": ""}
    client.force_login(user)
    response = client.post(reverse("post-create"), data=data)
    assert response.status_code == 200
    form = response.context["form"]
    assert "This field is required." in form.errors["title"]
    assert "This field is required." in form.errors["content"]


def test_add_post_unauthorized(client: Client, community: Community) -> None:
    data = {
        "community": community.pk,
        "title": "Test Post Title",
        "content": "This is a test post content.",
    }
    response = client.post(reverse("post-create"), data=data)
    assert response.status_code == 302
    assert reverse("login") in response.url


def test_post_delete(client: Client, create_post: Post) -> None:
    post = create_post
    delete_url = reverse("post-delete", args=[post.id])
    post_detail_url = reverse("post-detail", args=[post.id])
    post_list_url = reverse("post-list")

    response = client.get(post_detail_url)
    assert response.status_code == 200
    assert post.title in str(response.content)
    assert "Test Post Title" in str(response.content)

    response = client.get(post_list_url)
    assert response.status_code == 200
    assert post.title in str(response.content)
    assert "Test Post Title" in str(response.content)

    response = client.post(delete_url, follow=True)
    assert response.status_code == 200

    assert response.redirect_chain[0][0] == post_list_url

    response = client.get(post_detail_url)
    assert response.status_code == 404

    response = client.get(post_list_url)
    assert response.status_code == 200
    assert post.title not in str(response.content)
    assert "Test Post Titlex" not in str(response.content)

    assert not Post.objects.filter(id=post.id).exists()
