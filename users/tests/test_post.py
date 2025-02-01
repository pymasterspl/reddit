import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from core.models import Post

User = get_user_model()


@pytest.mark.django_db()
def test_edit_post_title(client: Client, user: User, post: Post) -> None:
    new_title = "Updated Title"
    url = reverse("edit_post", kwargs={"pk": post.id})
    client.force_login(user)
    response = client.post(url, {"title": new_title, "content": post.content, "id": post.id})
    post.refresh_from_db()
    assert response.status_code == 302
    assert post.title == new_title


@pytest.mark.django_db()
def test_edit_post_content(client: Client, user: User, post: Post) -> None:
    new_content = "Updated Content"
    url = reverse("edit_post", kwargs={"pk": post.id})
    client.force_login(user)
    response = client.post(url, {"title": post.title, "content": new_content, "id": post.id})
    post.refresh_from_db()
    assert response.status_code == 302
    assert post.content == new_content


@pytest.mark.django_db()
def test_edit_post_title_and_content(client: Client, user: User, post: Post) -> None:
    new_title = "Updated Title"
    new_content = "Updated Content"
    url = reverse("edit_post", kwargs={"pk": post.id})
    client.force_login(user)
    response = client.post(url, {"title": new_title, "content": new_content, "id": post.id})
    post.refresh_from_db()
    assert response.status_code == 302
    assert post.title == new_title
    assert post.content == new_content


@pytest.mark.django_db()
def test_delete_post(client: Client, user: User, post: Post) -> None:
    url = reverse("delete_post", kwargs={"pk": post.id})
    client.force_login(user)
    response = client.post(url)
    assert response.status_code == 302
    assert not Post.objects.filter(id=post.id).exists()
