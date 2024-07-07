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


def test_add_comment_valid(client: Client, user: User, post: Post) -> None:
    data = {
        "parent_id": post.pk,
        "content": "This is a test comment content.",
    }
    client.force_login(user)
    assert post.children_count == 0
    assert post.get_comments().count() == 0
    response = client.post(reverse("post-detail", kwargs={"pk": post.pk}), data=data, follow=True)
    assert response.status_code == 200
    assert post.children_count == 1
    assert post.get_comments().count() == 1
    post.refresh_from_db()
    assert response.context["comments"][0].author == user
    assert response.context["comments"][0].content == data["content"]


def test_add_comment_invalid(client: Client, user: User, post: Post) -> None:
    data = {"parent_id": post.pk, "content": ""}
    client.force_login(user)
    response = client.post(reverse("post-detail", kwargs={"pk": post.pk}), data=data)
    assert response.status_code == 200
    form = response.context["form"]
    assert len(form.errors) == 1
    assert "This field is required." in form.errors["content"]


def test_add_comment_valid_special_characters(client: Client, user: User, post: Post) -> None:
    data = {
        "parent_id": post.pk,
        "content": "This is a test comment with special characters! 😊🚀✨"
    }
    client.force_login(user)
    response = client.post(reverse("post-detail", kwargs={"pk": post.pk}), data=data, follow=True)
    assert response.status_code == 200
    new_comment = Post.objects.get(content=data["content"])
    assert new_comment.content == data["content"]


def test_add_comment_unauthorized(client: Client, post: Post) -> None:
    data = {
        "parent_id": post.pk,
        "content": "This is a test comment content.",
    }
    response = client.post(reverse("post-detail", kwargs={"pk": post.pk}), data=data)
    assert response.status_code == 302
    assert reverse("login") in response.url


def test_add_nested_comment_valid(client: Client, another_user: User, post: Post, comment: Post) -> None:
    data = {
        "parent_id": comment.pk,
        "content": "This is a test nested comment content.",
    }
    client.force_login(another_user)
    assert post.children_count == 1
    assert post.get_comments().count() == 1
    assert comment.children_count == 0
    assert comment.get_comments().count() == 0
    response = client.post(reverse("post-detail", kwargs={"pk": post.pk}), data=data, follow=True)
    assert response.status_code == 200
    post.refresh_from_db()
    comment.refresh_from_db()
    assert post.children_count == 2
    assert post.get_comments().count() == 1
    assert comment.children_count == 1
    assert comment.get_comments().count() == 1

    new_comment = Post.objects.get(content=data["content"])
    assert new_comment.author == another_user
    assert new_comment.parent == comment


def test_add_nested_comment_invalid(client: Client, user: User, post: Post, comment: Post) -> None:
    data = {
        "parent_id": comment.pk,
        "content": ""
    }
    client.force_login(user)
    response = client.post(reverse("post-detail", kwargs={"pk": post.pk}), data=data)
    assert response.status_code == 200
    form = response.context["form"]
    assert len(form.errors) == 1
    assert "This field is required." in form.errors["content"]


def test_add_nested_comment_unauthorized(client: Client, post: Post, comment: Post) -> None:
    data = {
        "parent_id": comment.pk,
        "content": "This is a test nested comment content.",
    }
    response = client.post(reverse("post-detail", kwargs={"pk": post.pk}), data=data)
    assert response.status_code == 302
    assert reverse("login") in response.url
